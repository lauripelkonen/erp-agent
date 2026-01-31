const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const path = require('path');

const outputDir = '/Users/lauripelkonen/Documents/Cursor/ERP-AGENT/website-project/pptx-output';

// Convert px to inches (96 DPI)
const px = (pixels) => pixels / 96;

// Calculate rectRadius for PptxGenJS (ratio relative to shorter dimension)
const calcRadius = (radiusPx, widthPx, heightPx) => {
  const shorterSide = Math.min(widthPx, heightPx);
  return radiusPx / shorterSide;
};

async function createDecorativeEllipse(filename) {
  // Purple blur element: 27% fill, progressive blur 68->100
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
    <defs>
      <filter id="blur" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="25"/>
      </filter>
      <radialGradient id="ellipseGrad" cx="50%" cy="50%" r="50%">
        <stop offset="0%" style="stop-color:#7c3aed;stop-opacity:0.27"/>
        <stop offset="68%" style="stop-color:#7c3aed;stop-opacity:0.18"/>
        <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:0"/>
      </radialGradient>
    </defs>
    <ellipse cx="150" cy="100" rx="120" ry="80" fill="url(#ellipseGrad)" filter="url(#blur)" transform="rotate(-12 150 100)"/>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(filename);
}

async function createCheckIcon(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 18 18">
    <circle cx="9" cy="9" r="8" fill="#22c55e" opacity="0.15"/>
    <path d="M5 9 L8 12 L13 6" stroke="#22c55e" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(filename);
}

async function createSpinnerIcon(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 18 18">
    <circle cx="9" cy="9" r="7" fill="none" stroke="#9ca3af" stroke-width="2" stroke-dasharray="12 6" stroke-linecap="round"/>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(filename);
}

async function createUserIcon(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 30 30">
    <circle cx="15" cy="11" r="5" fill="white"/>
    <ellipse cx="15" cy="26" rx="9" ry="6" fill="white"/>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(filename);
}

async function createAgentIcon(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 30 30">
    <rect x="3" y="3" width="24" height="24" rx="6" fill="#7c3aed"/>
    <circle cx="11" cy="13" r="2.5" fill="white"/>
    <circle cx="19" cy="13" r="2.5" fill="white"/>
    <path d="M10 19 Q15 23 20 19" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(filename);
}

async function main() {
  const ellipsePath = path.join(outputDir, 'ellipse.png');
  const checkPath = path.join(outputDir, 'check.png');
  const spinnerPath = path.join(outputDir, 'spinner.png');
  const userPath = path.join(outputDir, 'user.png');
  const agentPath = path.join(outputDir, 'agent.png');

  await Promise.all([
    createDecorativeEllipse(ellipsePath),
    createCheckIcon(checkPath),
    createSpinnerIcon(spinnerPath),
    createUserIcon(userPath),
    createAgentIcon(agentPath)
  ]);
  console.log('Assets created');

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title = 'Create an Offer';

  const slide = pptx.addSlide();
  slide.background = { color: 'EDEDED' };

  // === DIMENSIONS ===
  const cardW_px = 399, cardH_px = 429;
  const cardW = px(cardW_px), cardH = px(cardH_px);
  const cardX = (10 - cardW) / 2;
  const cardY = (5.625 - cardH) / 2;

  // Outer card - radius 25.5px
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: cardX, y: cardY, w: cardW, h: cardH,
    fill: { color: 'FFFFFF', transparency: 40 },
    shadow: { type: 'outer', blur: 8, offset: 2, angle: 135, color: '000000', opacity: 0.15 },
    rectRadius: calcRadius(25.5, cardW_px, cardH_px)
  });

  // Decorative purple blur ellipse
  slide.addImage({
    path: ellipsePath,
    x: cardX + px(150), y: cardY + px(30),
    w: px(180), h: px(130)
  });

  // Agent icon
  slide.addImage({
    path: agentPath,
    x: cardX + px(24), y: cardY + px(15),
    w: px(30), h: px(30)
  });

  // Title
  slide.addText('Create an Offer', {
    x: cardX + px(60), y: cardY + px(18),
    w: px(170), h: px(24),
    fontSize: 11, fontFace: 'Arial',
    color: '2600CC', bold: false
  });

  // === CHAT BUBBLE - radius 13.5px ===
  const bubbleW_px = 360, bubbleH_px = 69;
  const bubbleX = cardX + px(19.5);
  const bubbleY = cardY + px(55.5);

  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: bubbleX, y: bubbleY, w: px(bubbleW_px), h: px(bubbleH_px),
    fill: { color: '2600FF', transparency: 20 },
    shadow: { type: 'outer', blur: 6, offset: 2, angle: 63, color: '000000', opacity: 0.15 },
    rectRadius: calcRadius(13.5, bubbleW_px, bubbleH_px)
  });

  slide.addImage({
    path: userPath,
    x: bubbleX + px(10.5), y: bubbleY + px(19.5),
    w: px(30), h: px(30)
  });

  slide.addText('Check attached excel file and create an offer for Samsung Ltd including the products in it', {
    x: bubbleX + px(48), y: bubbleY + px(12),
    w: px(300), h: px(45),
    fontSize: 8, fontFace: 'Arial',
    color: 'FFFFFF', valign: 'middle'
  });

  // === ACTIONS CONTAINER - radius 13.5px ===
  const actionsW_px = 360, actionsH_px = 279;
  const actionsX = cardX + px(19.5);
  const actionsY = cardY + px(133.5);

  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: actionsX, y: actionsY, w: px(actionsW_px), h: px(actionsH_px),
    fill: { color: 'FFFFFF', transparency: 90 },
    shadow: { type: 'outer', blur: 10, offset: 2, angle: 63, color: '000000', opacity: 0.12 },
    rectRadius: calcRadius(13.5, actionsW_px, actionsH_px)
  });

  // === ACTION ITEMS - radius 7.5px ===
  const itemW_px = 333, itemH_px = 34.5;
  const actions = [
    { text: 'Calling extract_products_from_file', y: 13.86 },
    { text: 'Calling semantic_search', y: 55.5 },
    { text: 'Calling search_from_database', y: 97.5 },
    { text: 'Calling google_search', y: 139.5 },
    { text: 'Calling match_product_rows', y: 181.86 }
  ];

  actions.forEach((action) => {
    const itemX = actionsX + px(13);
    const itemY = actionsY + px(action.y);

    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: itemX, y: itemY, w: px(itemW_px), h: px(itemH_px),
      fill: { color: 'FFFFFF', transparency: 50 },
      shadow: { type: 'outer', blur: 3, offset: 1, angle: 90, color: '000000', opacity: 0.1 },
      rectRadius: calcRadius(7.5, itemW_px, itemH_px)
    });

    slide.addText(action.text, {
      x: itemX + px(9), y: itemY + px(6),
      w: px(265), h: px(24),
      fontSize: 9, fontFace: 'Arial',
      color: '6F6F6F', valign: 'middle'
    });

    slide.addImage({
      path: checkPath,
      x: itemX + px(292.5), y: itemY + px(8),
      w: px(18), h: px(18)
    });
  });

  // Spinner at top of actions
  slide.addImage({
    path: spinnerPath,
    x: actionsX + px(306), y: actionsY + px(22),
    w: px(18), h: px(18)
  });

  const outputPath = path.join(outputDir, 'create-offer-slide.pptx');
  await pptx.writeFile({ fileName: outputPath });
  console.log('PowerPoint created:', outputPath);
}

main().catch(console.error);
