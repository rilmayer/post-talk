const puppeteer = require('puppeteer');

const longLetter = {width: 3321, height: 1736};

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport(longLetter)
  await page.goto('https://example.com');
  await page.screenshot({path: 'output.png'});

  await browser.close();
})();