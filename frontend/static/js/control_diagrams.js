let img;
let currentImage = 'static/images/smartPowerStation_May1_2025-Controls.png';  // Initial image path

function setup() {
    let canvas = createCanvas(400, 300);
    canvas.parent('controlLogicContainer');  // Attach canvas to the div
    loadImage(currentImage, (loadedImg) => {
        img = loadedImg;
    });
}

function draw() {
    background(255);
    if (img) {
        image(img, 0, 0, width, height);
    }
}

window.changeImage = function changeImage(filename) {
    const fullPath = `${filename}`;
    loadImage(fullPath, (loadedImg) => {
        img = loadedImg;
    });
}