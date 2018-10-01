const puppeteer = require("puppeteer");
const AWS = require("aws-sdk");
const uuidV1 = require('uuid/v1');

const s3 = new AWS.S3();
const bucketName = "postalk.dev";
const longLetter = { width: 3321, height: 1736 };

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport(longLetter);
  await page.goto("http://localhost:5000");
  const blob = await page.pdf(longLetter);
  await browser.close();
  uploadS3(blob);  
})();

function uploadS3(blob) {
  s3.createBucket({ Bucket: bucketName }, function (err, data) {
    if (err) {
      console.log(err);
    }
    else {
      fileKey = uuidV1() + '.pdf';
      params = { Bucket: bucketName, Key: fileKey, Body: blob };
      s3.putObject(params, function (err, data) {
        if (err) {
          console.log(err);
        }
        else {
          console.log("Successfully uploaded data to " + fileKey);
        }
      });
    }
  });
}
