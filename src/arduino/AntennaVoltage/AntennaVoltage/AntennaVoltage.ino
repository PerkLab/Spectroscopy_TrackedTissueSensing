/*
antenna around cable 
*/

// constants won't change. They're used here to set pin numbers:
const int voltagePin = A1;     // the number of the hall effect sensor pin
const int RedPin =  3;     // the number of the LED pin
const int BluePin = 5;
const int GreenPin = 6;
const double changeThreshold = 0.3; // If the voltage changes by more than this, display a new voltage
double prevVoltage = 0;
// variables will change:
int voltageState = 0;          // variable for reading the hall sensor status
float timerMs = 0;
const float timerMaxMs = 1000; 
float currentTimeMs = 0;
const char END_OF_LINE_CHAR = 13; // CR
void setup() {
  // initialize the LED pin as an output:
  pinMode(RedPin, OUTPUT);
  pinMode(GreenPin, OUTPUT);
  pinMode(BluePin, OUTPUT);  
  // initialize the hall effect sensor pin as an input:
  pinMode(voltagePin, INPUT);
  Serial.begin(9600);  
}

void loop(){
  
  float lastTimeMs = currentTimeMs;
  currentTimeMs = millis();
  float deltaTimeMs = currentTimeMs - lastTimeMs;
  
  int voltageStateLastLoop = voltageState;
  
  // read the state of the antenna:
  voltageState = analogRead(voltagePin);
  float voltage=voltageState*(5.0/1023.0);
  
  //Serial.println(voltage);
  if ( (prevVoltage - voltage) > changeThreshold || (voltage - prevVoltage) > changeThreshold )
  {
    //Serial.println(prevVoltage);
    Serial.println(voltage);
    prevVoltage = voltage;
  }
  
  
  //0.1V=20.46
  //0.5v=102.3
  //1.0v=204.6
  //1.5v=306.9
  //2.0v=409.2
  //2.5v=511.5
  //3.0v=613.8
  //3.75v=767.25
  //4.0v=818.4
  //5.0v=1023
  
  if (timerMs > 0)
    timerMs = timerMs - deltaTimeMs;
  
  if (voltageState > 102.3 && voltageState <= 900) {   
    if (timerMs <= 0)
    {
      // turn LED red:    
      digitalWrite(RedPin, HIGH);
      digitalWrite(GreenPin, LOW);
      digitalWrite(BluePin, LOW);
    }
  } 
  else if (voltageState > 900 ){
    // turn LED blue:
    digitalWrite(RedPin, LOW);
    digitalWrite(BluePin, HIGH);
    digitalWrite(GreenPin, LOW);
    timerMs = timerMaxMs;
  }
  else {
   //turn LED off
    digitalWrite(RedPin, LOW);
    digitalWrite(GreenPin, LOW);
    digitalWrite(BluePin, LOW);
  } 
  
  }


