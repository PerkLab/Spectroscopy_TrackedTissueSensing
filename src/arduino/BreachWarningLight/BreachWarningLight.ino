/*
    taking input from slicer in the form of a 6 digit number to control colour, colour intensity, and flashing frequency of RGB LED
 first digit=colour intensity of red light, second digit=colour intensity of green light, third digit=colour intensity of blue light, fourth-sixth digits=frequency rate of blinking where 000-050 is solid and 999 is slowly blinking
 */
// communication protocol
const char END_OF_LINE_CHAR = 13; // CR
// arduino codes
const int ledREDPin = 6; //PWM Pin 6
const int ledGREENPin = 5; //PWM pin 5
const int ledBLUEPin = 3; //PWM pin 3
// store input
const int INPUT_ARRAY_LENGTH = 6;//length of input signal from slicer
const int INPUT_CHAR_MINIMUM = 0;//keyboard min int value
const int INPUT_CHAR_MAXIMUM = 9;//keyboard max int value
const int OUTPUT_INTENSITY_MINIMUM = 0;//arduino min input value
const int OUTPUT_INTENSITY_MAXIMUM = 255;//arduinio max input value
int inputArray[INPUT_ARRAY_LENGTH];
int inputArrayIndex = 0;
// indices
const int INPUT_ARRAY_INTENSITY_RED        = 0; // component intensities
const int INPUT_ARRAY_INTENSITY_GREEN      = 1;
const int INPUT_ARRAY_INTENSITY_BLUE       = 2;
const int INPUT_ARRAY_BLINK_INTERVAL_100 = 3; // frequency in hundreds
const int INPUT_ARRAY_BLINK_INTERVAL_10  = 4; // in tens
const int INPUT_ARRAY_BLINK_INTERVAL_1   = 5; // in last digit
// LED color
int intensityRed   = OUTPUT_INTENSITY_MINIMUM;
int intensityGreen = OUTPUT_INTENSITY_MINIMUM;
int intensityBlue  = OUTPUT_INTENSITY_MINIMUM;
// frequency-related
long previousMillis=0;//last time LED was updated
long interval=0;//interval of blinking
int currentlyBlinkedOn = 0; // 1 = on, 0 = off
String colorOutputString="";
// voltage reading related
const int voltagePin = A1;     // the input pin
const int ledPin =  13;     // the number of the LED pin
const double changeThreshold = 0.5; // If the voltage changes by more than this, display a new voltage
double prevVoltage = 0;
int voltageState = 0;          // variable for reading the voltage status



float linearWeight(int currentValue, int minValue, int maxValue)
{
  return (currentValue-minValue)/((float)(maxValue-minValue));
}
int linearInterpolation(float weight, int minValue, int maxValue)
{
  return (int)(minValue + weight*(maxValue-minValue));
}

void setup()
{
  pinMode(ledREDPin, OUTPUT); // Set output pins
  pinMode(ledGREENPin, OUTPUT);
  pinMode(ledBLUEPin, OUTPUT);
  pinMode(ledPin, OUTPUT);//initialize the built in LED on arduino
  pinMode(voltagePin, INPUT);//initialize the sensor pin as input
  // Start up serial connection
  Serial.begin(9600); // baud rate
  Serial.flush(); // waits for transmission of outgoing serial data to complete
}

void loop()
{
  //read the state of the antenna and print output voltage whenever voltage changes by more than 0.5V=change Threshold, turn on LED if voltage greater than 0.5v is detected
  Voltage_State_Function();
  Print_Voltage_State_Function();
  Test_LED_Function();
  
  while (Serial.available()>0)
  {
    //command = readCommand();
    char input = (char) Serial.read(); // Read in one char at a time
    //processCommand(command, response, r, g, b, f);
    if (input == END_OF_LINE_CHAR)
    {
      updateLEDParameters();
      updateColorOutputString();
      resettingInputArrayIndex();
      Serial.print("rgbfff=" + colorOutputString + END_OF_LINE_CHAR);
    }
    else
    { 
      if (inputArrayIndex >= INPUT_ARRAY_LENGTH)
      {
        tooManyCharactersWarning();
      }
      else
      {
        arrayInput(input);
      }    
    }

  }
    Frequency_timing_Function();
    Pin_input_Function();
}

void ParseInputArrayFunction (int index){

  switch (index)
  {
  case INPUT_ARRAY_INTENSITY_RED://make scale of 0 to 9 on a scale of 0 to 255 where 255 is brightest and 0 is off
    {
      float redWeight = 0;
      redWeight = linearWeight(inputArray[INPUT_ARRAY_INTENSITY_RED],INPUT_CHAR_MINIMUM,INPUT_CHAR_MAXIMUM);
      intensityRed = linearInterpolation(redWeight,OUTPUT_INTENSITY_MINIMUM,OUTPUT_INTENSITY_MAXIMUM);
      break;
    }
  case INPUT_ARRAY_INTENSITY_GREEN:
    {
      float greenWeight = 0;
      greenWeight = linearWeight(inputArray[INPUT_ARRAY_INTENSITY_GREEN],INPUT_CHAR_MINIMUM,INPUT_CHAR_MAXIMUM);
      intensityGreen = linearInterpolation(greenWeight,OUTPUT_INTENSITY_MINIMUM,OUTPUT_INTENSITY_MAXIMUM);
      break;
    }
  case INPUT_ARRAY_INTENSITY_BLUE:
    {
      float blueWeight = 0;
      blueWeight = linearWeight(inputArray[INPUT_ARRAY_INTENSITY_BLUE],INPUT_CHAR_MINIMUM,INPUT_CHAR_MAXIMUM);
      intensityBlue = linearInterpolation(blueWeight,OUTPUT_INTENSITY_MINIMUM,OUTPUT_INTENSITY_MAXIMUM);
      break;
    }
  case INPUT_ARRAY_BLINK_INTERVAL_100: // frequency in hundreds
    {
      interval += 100 * inputArray[INPUT_ARRAY_BLINK_INTERVAL_100];
      break;
    }
  case INPUT_ARRAY_BLINK_INTERVAL_10: // in tens
    {
      interval += 10 * inputArray[INPUT_ARRAY_BLINK_INTERVAL_10];
      break;
    }
  case INPUT_ARRAY_BLINK_INTERVAL_1: // in last digit
    {
      interval += inputArray[INPUT_ARRAY_BLINK_INTERVAL_1];
      break;
    }
  default:
    {
      String errorMessage = "Error: unexpected array index value in case 1. This should not happen - there is a bad coding error. LED output is likely meaningless.";
      Serial.print(errorMessage);
      break;
    }
  }
}

// update LED parameters according to array (updateLEDParameters)
// update color output string (updateColorOutputString)
// resetting inputArrayIndex

void updateLEDParameters()
{
  if (inputArrayIndex < INPUT_ARRAY_LENGTH)//if not enough input characters, give error message 
  {
    Serial.print("Not enough input characters provided. Using old values." + END_OF_LINE_CHAR);
  }

  intensityRed   = OUTPUT_INTENSITY_MAXIMUM;
  intensityGreen = OUTPUT_INTENSITY_MAXIMUM;
  intensityBlue  = OUTPUT_INTENSITY_MAXIMUM;
  interval = 0;
  for (inputArrayIndex = 0; inputArrayIndex < INPUT_ARRAY_LENGTH; inputArrayIndex++)
  {
    ParseInputArrayFunction(inputArrayIndex);
  }
}

void updateColorOutputString()
{
  colorOutputString = "";
  for (inputArrayIndex = 0; inputArrayIndex < INPUT_ARRAY_LENGTH; inputArrayIndex++)
  {
    colorOutputString = colorOutputString + inputArray[inputArrayIndex];
  }
}

void resettingInputArrayIndex()
{
  inputArrayIndex = 0; // reset the array index
}



//warning if too many characters inputed (toManyCharactersWarnging)
//add input to array and increase input array index (arrayInput)

void tooManyCharactersWarning()
{
  Serial.print("Too many input characters provided. Trunkating remainder.");
}
void arrayInput(int input)
{
  //Serial.print("Debug: CASE 2");
  int newInteger = (int)input - (int)'0';
  inputArray[inputArrayIndex] = newInteger;
  inputArrayIndex++;
}



//function for frequency times
// update blinker if needed
void Frequency_timing_Function()
{
  long currentMillis = millis();
  if (interval < 50)//if blinking rate is 50 or faster then it is so fast that it is always solid
  {
    currentlyBlinkedOn = 1;
  }
  else if (currentMillis-previousMillis>interval)
  {
    previousMillis=currentMillis;
    if (currentlyBlinkedOn == 1)
      currentlyBlinkedOn = 0;
    else
      currentlyBlinkedOn = 1;
  }
}
void Pin_input_Function()
//make a function for what ardruio sends to pins 
// output, handle LED color/lack thereof and output string to console
{
  if (currentlyBlinkedOn)//if currently low then turn it on
  {
    analogWrite(ledREDPin, intensityRed);
    analogWrite(ledGREENPin, intensityGreen); 
    analogWrite(ledBLUEPin, intensityBlue);

  }
  else//if currently high then turn it off
  {
    analogWrite(ledREDPin, OUTPUT_INTENSITY_MINIMUM);
    analogWrite(ledGREENPin, OUTPUT_INTENSITY_MINIMUM); 
    analogWrite(ledBLUEPin, OUTPUT_INTENSITY_MINIMUM);
  }
}
void Voltage_State_Function()
{
  voltageState = analogRead(voltagePin);
  float voltage=voltageState*(5.0/1023.0);
}
void Print_Voltage_State_Function()
{
  if ( (prevVoltage - voltage) > changeThreshold || (voltage - prevVoltage) > changeThreshold )
  {
    //Serial.println(prevVoltage);
    Serial.print(voltage + END_OF_LINE_CHAR);
    prevVoltage = voltage;
  }
}
void Test_LED_Function()
{
   if (voltageState > 102.3) {   
    // turn LED on:    
    digitalWrite(ledPin, HIGH);
    } 
  else {
    // turn LED off:
    digitalWrite(ledPin, LOW); 
  }
  //0.1V=20.46, 0.5v=102.3, 1.0v=204.6, 2.0v=409.2, 2.5v=511.5, 3.0v=613.8, 4.0v=818.4, 5.0v=1023
}

