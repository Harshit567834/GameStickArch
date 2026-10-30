#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>

WebServer server(80);
WiFiServer consoleServer(23);
WiFiClient consoleClient;
Preferences preferences;

void setup() {
  // GameStick uses 115200 baud for its serial console
  Serial.begin(115200);
  preferences.begin("modem", false);
  
  // Create our standalone setup network
  WiFi.softAP("GameStick-Terminal", "12345678");
  
  // Set up the Web server to accept Wi-Fi credentials from the Python GUI
  server.on("/setwifi", HTTP_POST, []() {
    String ssid = server.arg("ssid");
    String pass = server.arg("pass");
    
    preferences.putString("ssid", ssid);
    preferences.putString("pass", pass);
    
    server.send(200, "text/plain", "Credentials received. Rebooting ESP32 to connect...");
    delay(1000);
    ESP.restart();
  });
  
  server.begin();
  consoleServer.begin();

  // Check if we have saved Wi-Fi credentials to connect to
  String sta_ssid = preferences.getString("ssid", "");
  String sta_pass = preferences.getString("pass", "");
  
  if (sta_ssid.length() > 0) {
    WiFi.begin(sta_ssid.c_str(), sta_pass.c_str());
    int attempts = 0;
    // Don't block forever, just try 20 times (10 seconds)
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      MDNS.begin("gamestick");
    }
  }
}

void loop() {
  server.handleClient();
  
  // TCP to Serial Bridge (Raw Telnet)
  if (consoleServer.hasClient()) {
    if (consoleClient) consoleClient.stop();
    consoleClient = consoleServer.available();
    // Send a welcome message when someone connects
    consoleClient.println("\r\n--- ESP32 Wireless Serial Bridge Connected! ---");
    consoleClient.println("Press ENTER to wake up the GameStick console.\r\n");
  }

  if (consoleClient && consoleClient.connected()) {
    // If Python GUI sends data, push it to GameStick RX
    while (consoleClient.available()) {
      Serial.write(consoleClient.read());
    }
    // If GameStick TX sends data, push it to Python GUI
    while (Serial.available()) {
      consoleClient.write(Serial.read());
    }
  } else {
    // If no one is connected, flush the serial buffer so it doesn't back up
    while (Serial.available()) {
      Serial.read();
    }
  }
}