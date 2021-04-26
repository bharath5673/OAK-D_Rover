// Pin Numbers

int reverse_pin = 3;
int forward_pin = 4;
int enA = 5;
int enB = 6;
int left_pin = 7;
int right_pin = 8;

int buzzr = 12;

// duration for output
int time = 20;

// Initial command
int command = 0;


void setup() {
  // Set pins to OUTPUT mode
  pinMode(forward_pin, OUTPUT);
  pinMode(reverse_pin, OUTPUT);
  pinMode(enA, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(left_pin, OUTPUT);
  pinMode(right_pin, OUTPUT);
  pinMode(buzzr, OUTPUT);
  
  Serial.begin(115200);

//  bit_period = 1000000/115200;
}

void loop() {
  if (Serial.available() > 0)
  {
   command = Serial.read();
//   delay(3);
   delayMicroseconds(10);
  
  }
  else
  {
    reset();
  }
   drive(command);



//// buzzr tones

    if(command=='a')
    {
    for(int i; i< 10; i++)
    {
      digitalWrite(buzzr, i);           
      delay(100);
      digitalWrite(buzzr, 100);           
      delay(100);
      break;
      Serial.setTimeout(5); 
      while(command == '1');
      forward();  
    }
    }

    if(command=='b')
    {
    for(int i; i< 10; i++)
    {
      digitalWrite(buzzr, i);           
      delay(50);
      digitalWrite(buzzr, 100);           
      delay(50);
      break;
      Serial.setTimeout(5);
      while(command == '1');
      forward();
           
    }
    }


    if(command=='c')
    {      
    for(int i; i< 10; i++)
    {
      digitalWrite(buzzr, i);           
      delay(25);
      digitalWrite(buzzr, 100);           
      delay(25);
      break;
      Serial.setTimeout(5);
      while(command == '1');
      forward();  
    }
    }    

}

void reset()

{
  digitalWrite(forward_pin, LOW);
  digitalWrite(reverse_pin, LOW);
  digitalWrite(left_pin, LOW);
  digitalWrite(right_pin, LOW);
  analogWrite(buzzr, LOW);
}

// alternatively try 40/60, 250/500
void forward()
{
  digitalWrite(forward_pin, LOW);
  digitalWrite(forward_pin, HIGH);
  delay(time);
  Serial.print("Forward");
  analogWrite(enA, 75);
  analogWrite(enB, 150);
  Serial.setTimeout(5);
  
}

// alternatively try: 50/50
void reverse()
{

  digitalWrite(reverse_pin, LOW);
  digitalWrite(reverse_pin, HIGH);
  delay(time);
  Serial.print("Reverse");
  analogWrite(enA, 75);
  analogWrite(enB, 150);
  Serial.setTimeout(5);
  
//  while(command == 'b'); 
//    for(int i; i< 10; i++)
//    {
//      digitalWrite(buzzr, i);           
//      delay(50);
//      digitalWrite(buzzr, 100);           
//      delay(50);
//      break;
// 
//    }
//    Serial.setTimeout(5);


  while(command == 'b');
  { 
    digitalWrite(buzzr, 0);           
    delay(50);
    digitalWrite(buzzr, 100);           
    delay(50);
    digitalWrite(buzzr, 0);           
    delay(50);
    digitalWrite(buzzr, 100);           
    delay(50);
    digitalWrite(buzzr, 0);           
    delay(50);
    digitalWrite(buzzr, 100);           
    delay(50);
    digitalWrite(buzzr, 0);           
    delay(50);      
    digitalWrite(buzzr, 100);           
    delay(50); 
    digitalWrite(buzzr, 0);     
    delay(300);
    Serial.setTimeout(5);
  }

}

void left()
{
  digitalWrite(left_pin, LOW);
  digitalWrite(right_pin, HIGH);
  delay(time);
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}

void right()
{
  digitalWrite(left_pin, HIGH);
  digitalWrite(right_pin, LOW);
  delay(time);
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}

void forward_right()
{
  digitalWrite(left_pin, HIGH);
  digitalWrite(right_pin, LOW);
  forward();
  delay(time);  
  analogWrite(enA, 100);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}


void forward_left()
{
  digitalWrite(left_pin, LOW);
  digitalWrite(right_pin, HIGH);
  forward();
  delay(time);
  analogWrite(enA, 100);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}

void reverse_right()
{
  digitalWrite(left_pin, HIGH);
  digitalWrite(right_pin, LOW);
  reverse();
  delay(time);
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}

void reverse_left()
{
  digitalWrite(left_pin, LOW);
  digitalWrite(right_pin, HIGH);
  reverse();
  delay(time);
  analogWrite(enA, 150);
  analogWrite(enB, 150);
  Serial.setTimeout(5);

}


void Stop()

{
  digitalWrite(forward_pin, LOW);
  digitalWrite(reverse_pin, LOW);
  digitalWrite(left_pin, LOW);
  digitalWrite(right_pin, LOW);
  digitalWrite(buzzr, LOW);
}



void drive(int command)
{
  switch(command)
  {
    case 48: reset(); break;
    case 49: forward(); break;
    case 50: reverse(); break;
    case 51: right(); break;
    case 52: left(); break;
    case 53: forward_right(); break;
    case 54: forward_left(); break;
    case 55: reverse_right(); break;
    case 56: reverse_left(); break;
    default: Stop(); break;
    Serial.setTimeout(5);
  }
}