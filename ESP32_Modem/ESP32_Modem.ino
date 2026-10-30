#include <WiFi.h>
#include <ESPmDNS.h>
#include <Preferences.h>

Preferences preferences;
WiFiServer sshServer(22);
WiFiClient sshClient;

void setup() {
  Serial.begin(115200);
  preferences.begin("modem", false);
  
  // Set your WiFi credentials here if you don't want to use the serial commands
  String ssid = preferences.getString("ssid", "YOUR_WIFI_NAME");
  String pass = preferences.getString("pass", "YOUR_WIFI_PASSWORD");
  
  WiFi.begin(ssid.c_str(), pass.c_str());
  
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(500);
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    MDNS.begin("gamestick");
    sshServer.begin();
  }
}

void loop() {
  // Command mode for updating WiFi credentials over serial
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("CONNECT ")) {
      int firstSpace = cmd.indexOf(' ');
      int secondSpace = cmd.indexOf(' ', firstSpace + 1);
      if (secondSpace != -1) {
        String new_ssid = cmd.substring(firstSpace + 1, secondSpace);
        String new_pass = cmd.substring(secondSpace + 1);
        preferences.putString("ssid", new_ssid);
        preferences.putString("pass", new_pass);
        ESP.restart(); // Reboot to connect to new WiFi
      }
    }
  }

  // TCP to Serial Bridge for SSH
  if (sshServer.hasClient()) {
    if (sshClient) sshClient.stop();
    sshClient = sshServer.available();
  }

  if (sshClient && sshClient.connected()) {
    while (sshClient.available()) {
      Serial.write(sshClient.read());
    }
    while (Serial.available()) {
      sshClient.write(Serial.read());
    }
  }
}
