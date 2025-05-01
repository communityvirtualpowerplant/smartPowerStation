let img;
    let currentImage = 'static/images/image1.jpg';  // Initial image path

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

    function changeImage(filename) {
        const fullPath = `static/images/${filename}`;
        loadImage(fullPath, (loadedImg) => {
            img = loadedImg;
        });
    }