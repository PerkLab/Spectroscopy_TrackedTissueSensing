/*
antenna around cable 
*/

// constants won't change. They're used here to set pin numbers:
const int voltagePin = A1;     // the number of the hall effect sensor pin
const int ledPin =  13;     // the number of the LED pin
// variables will change:
int voltageState = 0;          // variable for reading the hall sensor status

void setup() {
  // initialize the LED pin as an output:
  pinMode(ledPin, OUTPUT);      
  // initialize the hall effect sensor pin as an input:
  pinMode(voltagePin, INPUT);
  Serial.begin(9600);  
}

void loop(){
  
  
  // read the state of the antenna:
  voltageState = analogRead(voltagePin);
  float voltage=voltageState*(5.0/1023.0);
  Serial.println(voltage);
  //0.1V=20.46
  //0.5v=102.3
  //1.0v=204.6
  //2.0v=409.2
  //2.5v=511.5
  //3.0v=613.8
  //4.0v=818.4
  //5.0v=1023
  
  if (voltageState > 20.46) {   
    // turn LED on:    
    digitalWrite(ledPin, HIGH);
    } 
  else {
    // turn LED off:
    digitalWrite(ledPin, LOW); 
  }
}

