#include <WiFi.h>
#include <esp_netif.h>
#include <netif/ppp/pppos.h>
#include <netif/ppp/ppp.h>
#include <Preferences.h>

Preferences preferences;
WiFiServer sshProxy(22);
WiFiClient sshClient;
WiFiClient sshTarget;

ppp_pcb *ppp;
struct netif ppp_netif;
bool ppp_active = false;

static void ppp_status_cb(ppp_pcb *pcb, int err_code, void *ctx) {
  if (err_code == PPPERR_NONE) {
    ppp_active = true;
  } else {
    ppp_active = false;
  }
}

static u32_t ppp_output_cb(ppp_pcb *pcb, u8_t *data, u32_t len, void *ctx) {
  return Serial.write(data, len);
}

void setup() {
  Serial.begin(115200);
  preferences.begin("modem", false);
}

void loop() {
  static bool in_command_mode = true;
  static unsigned long last_plus_time = 0;
  static int plus_count = 0;

  if (in_command_mode) {
    if (Serial.available()) {
      String cmd = Serial.readStringUntil('\n');
      cmd.trim();
      
      if (cmd == "SCAN") {
        int n = WiFi.scanNetworks();
        for (int i = 0; i < n; ++i) {
          Serial.println(WiFi.SSID(i));
        }
        Serial.println("SCAN_DONE");
      } 
      else if (cmd.startsWith("CONNECT ")) {
        int firstSpace = cmd.indexOf(' ');
        int secondSpace = cmd.indexOf(' ', firstSpace + 1);
        if (secondSpace != -1) {
          String new_ssid = cmd.substring(firstSpace + 1, secondSpace);
          String new_pass = cmd.substring(secondSpace + 1);
          preferences.putString("ssid", new_ssid);
          preferences.putString("pass", new_pass);
          Serial.println("OK");
        }
      }
      else if (cmd == "START") {
        String ssid = preferences.getString("ssid", "");
        String pass = preferences.getString("pass", "");
        
        if (ssid.length() > 0) {
          WiFi.begin(ssid.c_str(), pass.c_str());
          int attempts = 0;
          while (WiFi.status() != WL_CONNECTED && attempts < 20) {
            delay(500);
            attempts++;
          }
        }

        esp_netif_init();
        ppp = pppos_create(&ppp_netif, ppp_output_cb, ppp_status_cb, NULL);
        if (ppp) {
          ppp_set_default(ppp);
          ppp_set_usepeerdns(ppp, 1);
          ppp_connect(ppp, 0);
          
          // Enable NAPT (Network Address and Port Translation) for internet access
          #if defined(ESP_IDF_VERSION) && ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 4, 0)
          esp_netif_t *netif_sta = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
          if (netif_sta) {
              esp_netif_napt_enable(netif_sta);
          }
          #endif
          
          in_command_mode = false;
          sshProxy.begin();
          Serial.println("PPP_STARTED");
        }
      }
    }
  } else {
    // PPP Mode
    // Handle SSH Proxy
    if (sshProxy.hasClient()) {
      if (sshClient) sshClient.stop();
      sshClient = sshProxy.available();
      if (sshTarget) sshTarget.stop();
      sshTarget.connect("10.0.0.1", 22);
    }
    
    if (sshClient && sshClient.connected() && sshTarget && sshTarget.connected()) {
      size_t c_avail = sshClient.available();
      if (c_avail > 0) {
        uint8_t buf[128];
        size_t len = sshClient.read(buf, min(c_avail, sizeof(buf)));
        sshTarget.write(buf, len);
      }
      size_t t_avail = sshTarget.available();
      if (t_avail > 0) {
        uint8_t buf[128];
        size_t len = sshTarget.read(buf, min(t_avail, sizeof(buf)));
        sshClient.write(buf, len);
      }
    } else {
      if (sshClient) sshClient.stop();
      if (sshTarget) sshTarget.stop();
    }

    while (Serial.available()) {
      uint8_t buffer[128];
      int len = Serial.readBytes(buffer, sizeof(buffer));
      
      // Check for +++ escape sequence
      for (int i = 0; i < len; i++) {
        if (buffer[i] == '+') {
          unsigned long now = millis();
          if (now - last_plus_time > 1000) plus_count = 0;
          plus_count++;
          last_plus_time = now;
          if (plus_count == 3) {
            // Escape to command mode
            if (ppp) {
              ppp_close(ppp, 0);
              ppp_free(ppp);
              ppp = NULL;
            }
            WiFi.disconnect();
            in_command_mode = true;
            plus_count = 0;
            Serial.println("\nOK");
            return;
          }
        } else {
          plus_count = 0;
        }
      }
      
      if (len > 0 && ppp) {
        pppos_input(ppp, buffer, len);
      }
    }
  }
}
