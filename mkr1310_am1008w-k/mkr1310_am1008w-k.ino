#include <MKRWAN.h>
#include <am1008w_k_i2c.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include "arduino_secrets.h"

LoRaModem modem;
LiquidCrystal_I2C lcd(0x27, 16, 2);     // lcd i2c address : 0x27, 16x2 lcd
AM1008W_K_I2C am1008w_k_i2c;            // am1008w-k i2c address : 0x28

String appEui = SECRET_APP_EUI;   // application EUI for OTAA
String appKey = SECRET_APP_KEY;   // application key for OTAA

int packet_id = 0; // packet counter
int period = 15; // min
bool mode = false;  // true : confirmed mode, false : unconfirmed mode
char cursor0[17];
char cursor1[17];

typedef struct packet_s 
{ 
  uint16_t voc;          // 2byte
  uint16_t co2;          // 2byte
  uint16_t humidity;     // 2byte
  uint16_t temp;         // 2byte 
  uint8_t pm1p0;         // 1byte
  uint8_t pm2p5;         // 1byte
  uint8_t pm10;          // 1byte
  uint8_t now_r_ref_r;   // 1byte
  uint16_t ref_r;        // 2byte
  uint16_t now_r;        // 2byte
}Packet_s;  //16byte
   
typedef union packet_u 
{ 
  Packet_s ps;  
  uint8_t pl[16]; 
}Packet_u;

Packet_u packet_data;


void setup() {
  pinMode(LED_BUILTIN, OUTPUT);  //led 13
  lcd.init();  // lcd init
  lcd.backlight();  // lcd backlight
  am1008w_k_i2c.begin();  // am1008w-k init
  delay(1000);

  lcd.setCursor(0,0);
  (mode == true) ? (lcd.print("confirmed mode")) : (lcd.print("unconfirmed mode"));
  lcd.setCursor(0,1);
  lcd.print("OTAA Join...");
  
  if (!modem.begin(KR920)) {  // lorawan regional parameter : kr920
    while (1) {}
  };

  bool adr = modem.setADR(true);

  int connected = modem.joinOTAA(appEui, appKey);  // OTAA

  if (!connected) {
    while (1) {}
  }

  modem.minPollInterval(60);

  // initialize packet
  packet_data.ps.co2 = 0;
  packet_data.ps.voc = 0;
  packet_data.ps.humidity = 0;
  packet_data.ps.temp = 0;
  packet_data.ps.pm1p0 = 0;
  packet_data.ps.pm2p5 = 0;
  packet_data.ps.pm10 = 0;
  packet_data.ps.now_r_ref_r = 0;
  packet_data.ps.ref_r = 0;
  packet_data.ps.now_r = 0;

  lcd.clear();  // lcd clear
}

void loop() 
{
  digitalWrite(LED_BUILTIN, HIGH);
  uint8_t ret = am1008w_k_i2c.read_data_command();

  packet_data.ps.co2 = am1008w_k_i2c.get_co2();
  packet_data.ps.voc = am1008w_k_i2c.get_voc();
  packet_data.ps.humidity = uint16_t(am1008w_k_i2c.get_humidity()*100);
  packet_data.ps.temp = uint16_t(am1008w_k_i2c.get_temperature()*100);
  packet_data.ps.pm1p0 = am1008w_k_i2c.get_pm1p0();
  packet_data.ps.pm2p5 = am1008w_k_i2c.get_pm2p5();
  packet_data.ps.pm10 = am1008w_k_i2c.get_pm10();
  packet_data.ps.now_r_ref_r = am1008w_k_i2c.get_voc_now_r_ref_r();
  packet_data.ps.ref_r = am1008w_k_i2c.get_voc_ref_r();
  packet_data.ps.now_r = am1008w_k_i2c.get_voc_now_r();
  
  lcd.setCursor(0,0);
  sprintf(cursor0, "period %d min", period);
  lcd.print(cursor0);
  lcd.setCursor(0,1);
  sprintf(cursor1, "packet %d", packet_id);
	lcd.print(cursor1);

  modem.beginPacket();
  int err = modem.write(packet_data.pl, sizeof(packet_data.pl));
  err = modem.endPacket(mode);  // unconfirmed mode
  if(modem.available()) period = modem.read();

  packet_id++;
  digitalWrite(LED_BUILTIN, LOW);
  
  delay(60*1000*period);  // 60 sec x period
  lcd.clear();  // lcd clear
}