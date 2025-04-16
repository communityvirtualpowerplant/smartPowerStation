function setup() {
  let canvas = createCanvas(700, 500);
  canvas.parent('statusCanvasContainer'); // Attach to the specific div
}

function draw() {
  background(220);
  drawSystem();
  //animateResponse();
}

function drawSystem() {
  let centerH = height/2;
  let centerW = width/2;
  
  textSize(14);
  textAlign(CENTER);
  fill(0);
  stroke(0);
  
  let batWidth = 100
  let batCenterX = width/2
  let batHeight = 75
  let batCenterY = height/2-batHeight*1.25;
  let batP=.76
  let batH = 160
  let relay1H = batCenterY
  let smCenterY = height/2+batHeight*1.25;

  // Draw wires and connections
  drawWire([[100, centerH, 200, centerH],[200, centerH, 200, batCenterY],[200, batCenterY, batCenterX-batWidth/2, batCenterY]],true); // Grid to battery
  drawWire([[100, centerH, 200, centerH],[200, centerH, 200, smCenterY],[200, smCenterY, 500, smCenterY],[500, smCenterY, 500, centerH+25]],false);// Grid to transfer switch
  drawWire([[batCenterX+batWidth/2, batCenterY, 500, batCenterY],[500, batCenterY, 500, centerH-25]],true); // Battery to transfer switch
  drawWire([[525, centerH, 590, centerH]],true); // transfer switch to Load
  
  
  // Draw grid power source
  fill(150);
  circle(90, centerH, 20); // Grid Source Box
  fill(0);
  let gridV = 120
  underText("Grid\n"+ gridV +" VAC", 90, centerH+20);
  
  // Draw load
  fill(150);
  circle(600, centerH, 20); // Grid Source Box
  fill(0);
  let loadW = 23
  underText("Load\n" +loadW +" Watts", 600, centerH+20);
 
  // Draw battery system
  push()
  
    rectMode(CORNER);
    fill(255)
    noStroke()
    rect(batCenterX-batWidth/2, batCenterY-batHeight/2+batHeight-(batHeight*batP), batWidth, batHeight*batP); // Battery Box
    stroke(0)
    noFill()
    rect(batCenterX-batWidth/2, batCenterY-batHeight/2, batWidth, batHeight); // Battery Box Outline
    underText("Battery\n" + batP*100 +"%", batCenterX, batCenterY+batHeight/2+10);
  pop()
  
   // Draw Smart Relay 1
  rectMode(CENTER);
  fill(255)
  rect(200, batCenterY, 10,10); // Battery Box
  leftText("130W", 190, batCenterY);
  fill(200)
  triangle(195, batCenterY+5, 200, batCenterY-5, 205, batCenterY+5);

  // Draw Smart Relay 2
  rectMode(CENTER);
  fill(255)
  rect(200, smCenterY, 10,10); // Battery Box
  leftText("0W", 190, smCenterY);
  fill(200)
  triangle(195, smCenterY+5, 200, smCenterY-5, 205, smCenterY+5);

  // Draw Smart Relay 3
  rectMode(CENTER);
  fill(255)
  rect(500, batCenterY, 10,10); // Battery Box
  leftText("23W", 500, batCenterY-20);

  // Draw Transfer Switch
  push()
    rectMode(CENTER);
    stroke(0)
    fill(150)
    rect(500, centerH, 50,50); // Battery Box
    noFill()
    stroke(200, 150, 255);
    strokeWeight(6);
    arc(500, centerH, 40, 40, PI+HALF_PI,0);
    stroke(0)
    strokeWeight(2);
    arc(500, centerH, 40, 40, PI+HALF_PI,0);
    leftText("Transfer\n Switch", 470, centerH);
  pop()

  textAlign(CENTER,CENTER)
  fill(0) 
  noStroke()
  textSize(20)
  text("Demand Response Behind-The-Meter (BTM) System", centerW, 50);
  
//   text(gridV + "VAC", 50, centerH)
  
//   let invV = 120
//   text(invV + "VAC", 500, batCenterY)
  
    drawKey()
}

// let batteryDischarge = false;
// let dotX = 110;
// let dotY = 230;

function drawKey(){
  push()
    textSize(14);

    rectMode(CENTER);
    stroke(0)
    fill(255)
    rect(20, height-20, 10,10);
    rect(150, height-20, 10,10);
    fill(200)
    triangle(15, height-15, 20, height-25, 25, height-15);

    drawWire([[220,height-20, 250,height-20]],false)

    drawWire([[305,height-20, 335,height-20]],true)

    noStroke(0)
    fill(0)
    textAlign(LEFT)
    text("Relay & Sensor", 30, height-20);
    text("Sensor", 160, height- 20);
    text("Dead", 255, height-20)
    text("Live", 340, height-20)
  pop()
}

function underText(t,x,y){
  push()
    noStroke();
    textAlign(CENTER, CENTER);
    fill(0);
    text(t, x,y+10);
    fill(150);
  pop()
}

function leftText(t,x,y){
  push()
    noStroke();
    textAlign(RIGHT);
    fill(0);
    text(t, x,y);
    fill(150);
  pop()
}

function drawWire(a,state){
  push();
    if (state==true){
      stroke(200, 150, 255);
      strokeWeight(6);
      for (let w in a){
        c = a[w]
        line(c[0],c[1],c[2],c[3]);
      }
    }
  
    strokeWeight(2);
    stroke(0);
    for (let w in a){
        c = a[w]
        line(c[0],c[1],c[2],c[3]);
      }
  pop()
}

// function animateResponse() {
//   fill(255, 0, 0);
//   ellipse(dotX, dotY, 10, 10); // Power flow indicator
  
//   if (batteryDischarge) {
//     dotX += 2; // Move dot from battery to load
//     if (dotX > 550) {
//       dotX = 380;
//     }
//   } else {
//     dotX += 2; // Move dot from grid to load
//     if (dotX > 550) {
//       dotX = 110;
//     }
//   }
// }
