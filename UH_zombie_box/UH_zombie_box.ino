// For the locked box that is opened by the zombie -- system includes ESP8266 and a relay to
// open the box. The ESP8266 connects to the MQTT broker and unlocks  the box  when it
// receives the proper MQTT message.
//
// Revision history:
//  1.0 (2/20/2019) Initial version
#define BOX_DEBUG

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoOTA.h>
#include <EEPROM.h>
#include "MQTT.h"

// Relay controls
const int OFF = 0;             // relay is active high
const int ON = 1;

const int LED = 0;            // pin for the onboard LED

// Pin controlling the electromagnet
const int MAGLOCK = 15;


// WiFi config
const char ssid[] = "unlockedhistory_local";
const char passwd[] = "IDx1bEp9qgInIzvJ";

// OTA config
const char OTAName[] = "UH_Zombie_Box";         // A name and a password for the OTA service
const char OTAPassword[] = "";

// standard MQTT setup
const unsigned int mqttPort = 1883;
const char brokerIpAddr[] = "192.168.1.10";
MQTT mqtt("ZombieBox", brokerIpAddr, mqttPort);
bool connectedToBroker = false;

// web server
const char webserverIpAddr[] = "192.168.1.10";
const int webserverPort = 80;

// status of the maglock
int maglockLocked = 0;

// whether to send web update
bool sendWebUpdate = false;

//*************************************************************************
// Function prototypes
//*************************************************************************
void connectWifi();                           // wifi access point setup
void setupOTA();                          // Over The Air software updates

void lockBox();
void unlockBox();

// handle MQTT message
void myCallback(uint32_t *client, const char* topic, uint32_t topicLen,
                   const char *data, uint32_t dataLen);

// talk to web server
void initWebStatus(int status);
void updateWebStatus(int status);

//********************************************************************************
// Initialize the system. Set up all the servers and initialize the relay
// controlling the  lock.
//********************************************************************************
void setup()
{
  // set up serial port for diagnostics
  Serial.begin(115200);
  Serial.println();

  pinMode(LED, OUTPUT);

  // digital out for the lock
  pinMode(MAGLOCK, OUTPUT);

  // connect to the wifi network
  connectWifi();

  // set up the OTA server for updates
  setupOTA();

  // connect to mqtt broker
  setupMqtt();
  connectMqtt();

  // send initial status to web server
  initWebStatus(maglockLocked);
  
  // lock the box initially
  lockBox();

}


//************************************************************************
// loop -- handle OTA requests.
// Note that MQTT requests are handled elsewhere by the callback functions.
//************************************************************************
void loop(void) { 
  // check for OTA updates
  ArduinoOTA.handle();

  // update the web page?
  if (sendWebUpdate) {
    sendWebUpdate = false;

    updateWebStatus(maglockLocked);  
  }
  
  // wait a little bit
  delay(10);
}


//******************************************************************************************
// Set up wifi connection, keep trying until successful. If we can't connect after several
// seconds, we give up (the server must be down). We then delay 30 seconds and reset ourself.
//******************************************************************************************
void connectWifi()
{
  bool connectedWifi = false;

  // connect to wifi access point
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, passwd);
  WiFi.mode(WIFI_STA);                // internet advice (but untested) -- set mode both before
  // and after begin() to make sure


#ifdef BOX_DEBUG
  Serial.print("Starting WiFi connection: ");
#endif

  // wait for connection
  for (int i = 0; !connectedWifi && i < 1000; ++i) {
#ifdef BOX_DEBUG
    Serial.print(".");
#endif

    delay(10);

    connectedWifi = (WiFi.status() == WL_CONNECTED);
  }

  // did we connect or timeout?
  if (!connectedWifi)  {
    // still not connected, so reset the system
#ifdef BOX_DEBUG
    Serial.println("Can't connect to WiFi, retrying in 30 seconds.");
#endif

    // blink LED 3 times, repeat 30 times
    for (int i = 0; i < 30; i++) {
      for (int j = 0; j  < 3; j++)  {
        digitalWrite(LED, ON);
        delay(125);
        digitalWrite(LED, OFF);
        delay(125);
      }
      delay(250);
    }

    ESP.restart();
  }

  else {
#ifdef BOX_DEBUG
    Serial.println("Connected");
#endif
  }

}

//*****************************************************************************
// Disconnect from wifi network.
//*****************************************************************************
void disconnectWifi()
{
  WiFi.disconnect();
}


//*****************************************************************************
// Setup the callback functions for the MQTT connection.
//*****************************************************************************
void setupMqtt()
{
  // set up callback functions
  mqtt.onConnected(mqttConnectedCb);
  mqtt.onDisconnected(mqttDisconnectedCb);
  mqtt.onData(mqttDataCb);
}


//******************************************************************************
// Connect to mqtt broker. Note that if connection can't be made, this routine will restart the ESP
//******************************************************************************
void connectMqtt()
{
#ifdef BOX_DEBUG
  Serial.println("Connecting to MQTT broker");
#endif
  // connect to the broker
  mqtt.connect();

  // wait until we're connected
  for (int i = 0; !connectedToBroker && i < 1000; ++i) {
    delay(20);
  }

  // if still not connected, restart
  if (!connectedToBroker) {
#ifdef BOX_DEBUG
    Serial.println("Can't connect to MQTT broker -- restarting in 30 seconds");
#endif

    // blink 4 times for 30 sec
    for (int i = 0; i < 30; i++) {
      for (int j = 0; j < 4; j++) {
        digitalWrite(LED, ON);
        delay(100);
        digitalWrite(LED, OFF);
        delay(100);
      }
      delay(200);
    }
 
    ESP.restart();
  }

}


//*****************************************************************************************
// Disconnect from the MQTT server.
//*****************************************************************************************
void disconnectMqtt()
{
  mqtt.disconnect();

  // wait until we disconnect
  for (int i = 0; connectedToBroker && i < 1000; ++i) {
    delay(10);
  }

  if (connectedToBroker) {
#ifdef BOX_DEBUG
    Serial.println("Can't disconnect from MQTT broker -- restarting in 10 seconds");
#endif

    delay(10000);
    ESP.restart();
  }
}



//****************************************************************************************
// Set up the Over The Air service. This handles updates to the software.
//****************************************************************************************
void setupOTA()
{
  ArduinoOTA.setHostname(OTAName);
  ArduinoOTA.setPassword(OTAPassword);

  // set up the callbacks
  ArduinoOTA.onStart([]() {
#ifdef BOX_DEBUG
    Serial.println("Start");
#endif
  });

  ArduinoOTA.onEnd([]() {
#ifdef BOX_DEBUG
    Serial.println("\r\nEnd");
#endif
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
#ifdef BOX_DEBUG
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
#endif
  });

  ArduinoOTA.onError([](ota_error_t error) {
#ifdef BOX_DEBUG
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
#endif
  });

  ArduinoOTA.begin();

#ifdef BOX_DEBUG
  Serial.println("OTA ready");
#endif
}



//*******************************************************************************
// Callback when connected to MQTT broker. We update the status variables and
// turn on the LED for visual status.
//*******************************************************************************
void mqttConnectedCb()
{
#ifdef BOX_DEBUG
  Serial.println("connected to MQTT server");
#endif

  connectedToBroker = true;

  // subscribe to zombielock msgs
  mqtt.subscribe("zombielock");

  // turn off led for visual check
  digitalWrite(LED, HIGH);
}

//**********************************************************************************
// Callback when disconnected from MQTT broker. We try to re-connect.
//**********************************************************************************
void mqttDisconnectedCb()
{
#ifdef BOX_DEBUG
  Serial.println("Disconnected");
#endif

  // update status variables
  connectedToBroker = false;

  // turn on led since we're not connected
  digitalWrite(0, LOW);

  // try to reconnect
  disconnectWifi();             // see if resetting wifi helps
  connectWifi();
  connectMqtt();

}

//**********************************************************************************
// Callback when  a message is received. We update the lock.
//**********************************************************************************
void mqttDataCb(String& topic, String& payload)
{
  if (topic == "zombielock") {
    // message is for us
    if (payload == "lock") {
#ifdef BOX_DEBUG
      Serial.println("Locking box");
#endif

      lockBox();
    }
    else if (payload == "unlock") {
#ifdef BOX_DEBUG
      Serial.println("Unlocking box");
#endif

      unlockBox();
    }
  }
}






//************************************************************************
// Open the box lock
//************************************************************************
void unlockBox()
{
  // turn the magnet off to open the box
  digitalWrite(MAGLOCK, OFF);

  digitalWrite(LED, HIGH);        // turn LED off too for diagnostics

  // update status on web server
  maglockLocked = 0;
  sendWebUpdate = true;
}

//************************************************************************
// Lock the box
//************************************************************************
void lockBox()
{
  // turn the magnets on to lock the box
  digitalWrite(MAGLOCK, ON);

  digitalWrite(LED, LOW);        // turn LED on too for diagnostics

  // update status on web server
  maglockLocked = 1;
  sendWebUpdate = true;
}

//*****************************************
// Initialize status on web page
//*****************************************
void initWebStatus(int status)
{
  WiFiClient client;
  HTTPClient http;
  String postData = "lockname=Box&status=" + String(status);
  Serial.println("Init: " + postData);

  http.begin(client, "http://192.168.1.10/initlock");
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  int result = http.POST(postData);
  http.writeToStream(&Serial);
  http.end();
}

//*****************************************
// Update status on web page
//*****************************************
void updateWebStatus(int status)
{
  WiFiClient client;
  HTTPClient http;
  String postData = "lockname=Box&status=" + String(status);
  Serial.println("Update: " + postData);

  http.begin(client, "http://192.168.1.10/updatelock");
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  int result = http.POST(postData);
  http.writeToStream(&Serial);
  http.end();
}

