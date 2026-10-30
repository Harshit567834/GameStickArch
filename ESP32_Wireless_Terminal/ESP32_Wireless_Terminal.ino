#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <esp_netif.h>
#include <netif/ppp/pppos.h>
#include <netif/ppp/ppp.h>

extern "C" {
  // Weakly declare NAPT enable so it compiles perfectly on older Arduino cores (which lack NAT).
  // This bypasses the fatal compiler error you were getting!
  esp_err_t esp_netif_napt_enable(void *esp_netif) __attribute__((weak));
}

WebServer server(80);
WiFiServer consoleServer(23);
WiFiClient consoleClient;
Preferences preferences;

ppp_pcb *ppp = NULL;
struct netif ppp_netif;
bool ppp_mode = false;

static void ppp_status_cb(ppp_pcb *pcb, int err_code, void *ctx) {}

static u32_t ppp_output_cb(ppp_pcb *pcb, u8_t *data, u32_t len, void *ctx) {
  return Serial.write(data, len);
}

void start_ppp() {
  if (ppp != NULL) return;
  esp_netif_init();
  ppp = pppos_create(&ppp_netif, ppp_output_cb, ppp_status_cb, NULL);
  if (ppp) {
    ppp_set_default(ppp);
    ppp_set_usepeerdns(ppp, 1);
    ppp_connect(ppp, 0);

    // If the Arduino core has NAPT support, we enable it. If not, it just ignores it gracefully.
    esp_netif_t *netif_sta = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (netif_sta && esp_netif_napt_enable != NULL) {
        esp_netif_napt_enable((void*)netif_sta);
    }
  }
  ppp_mode = true;
}

void setup() {
  Serial.begin(115200);
  preferences.begin("modem", false);
  
  WiFi.softAP("GameStick-Terminal", "12345678");
  
  server.on("/setwifi", HTTP_POST, []() {
    String ssid = server.arg("ssid");
    String pass = server.arg("pass");
    preferences.putString("ssid", ssid);
    preferences.putString("pass", pass);
    server.send(200, "text/plain", "Credentials received. Rebooting ESP32...");
    delay(1000);
    ESP.restart();
  });
  
  server.begin();
  consoleServer.begin();

  String sta_ssid = preferences.getString("ssid", "");
  String sta_pass = preferences.getString("pass", "");
  
  if (sta_ssid.length() > 0) {
    WiFi.begin(sta_ssid.c_str(), sta_pass.c_str());
    int attempts = 0;
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
  
  if (!ppp_mode) {
    // TCP to Serial Bridge Mode
    if (consoleServer.hasClient()) {
      if (consoleClient) consoleClient.stop();
      consoleClient = consoleServer.available();
      consoleClient.println("\r\n--- ESP32 Wireless Serial Bridge Connected! ---");
      consoleClient.println("Press ENTER to wake up the GameStick console.\r\n");
    }

    if (consoleClient && consoleClient.connected()) {
      while (consoleClient.available()) {
        Serial.write(consoleClient.read());
      }
    }
    
    // Check incoming serial for trigger command
    while (Serial.available()) {
      char c = Serial.read();
      static int trigger_idx = 0;
      const char* trigger = "+++PPP";
      
      if (c == trigger[trigger_idx]) {
        trigger_idx++;
        if (trigger_idx == 6) {
          if (consoleClient) {
            consoleClient.println("\r\n[Switching to Full Internet Modem Mode...]");
            consoleClient.stop();
          }
          start_ppp();
          return;
        }
      } else {
        trigger_idx = (c == trigger[0]) ? 1 : 0;
      }
      
      if (consoleClient && consoleClient.connected()) {
        consoleClient.write(c);
      }
    }
  } else {
    // PPP Mode - raw binary framing
    while (Serial.available()) {
      uint8_t buffer[128];
      int len = Serial.readBytes(buffer, sizeof(buffer));
      if (len > 0 && ppp) {
        pppos_input(ppp, buffer, len);
      }
    }
  }
}
