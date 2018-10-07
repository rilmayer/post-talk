const AWS = require('aws-sdk');
const launchChrome = require('@serverless-chrome/lambda');
const CDP = require('chrome-remote-interface');
const puppeteer = require('puppeteer');
const uuidv1 = require('uuid/v1');
const child_process = require('child_process');
const fs = require('fs');

const SAVE_BUCKET_NAME = 'postalk.dev';
process.env['PATH'] = process.env['PATH'] + ':' + process.env['LAMBDA_TASK_ROOT'] + '/bin';
process.env['LD_LIBRARY_PATH'] = process.env['LAMBDA_TASK_ROOT'] + '/bin';

exports.handler = async (event, context, callback) => {
    let slsChrome = null;
    let browser = null;
    let page = null;

    try {
        const data = JSON.parse(event.body);
        const urlParams = "?message=" + data.message.join('\n') +
            "&sender_name=" + data.sender_name +
            "&sender_address=" + data.sender_address +
            "&sender_postal_code=" + data.sender_postal_code +
            "&receiver_name=" + data.receiver_name +
            "&receiver_address=" + data.receiver_address +
            "&receiver_postal_code=" + data.receiver_postal_code

        slsChrome = await launchChrome();
        browser = await puppeteer.connect({
            browserWSEndpoint: (await CDP.Version()).webSocketDebuggerUrl
        });
        page = await browser.newPage();
        await page.goto('https://postalk-letter-dev.herokuapp.com/letter_front' + urlParams, {
            waitUntil: 'domcontentloaded'
        });
        await page.waitFor(1000)
        await page.pdf({
            path: "/tmp/front.pdf",
            width: '250mm',
            height: '176mm',
            printBackground: true
        });

        await page.goto('https://postalk-letter-dev.herokuapp.com/letter_back' + urlParams, {
            waitUntil: 'domcontentloaded'
        });
        await page.waitFor(1000)
        await page.pdf({
            path: "/tmp/back.pdf",
            width: '250mm',
            height: '176mm',
            printBackground: true
        });

        const outputFileName = '/tmp/output.pdf';
        child_process.execSync('pdftk A=/tmp/front.pdf B=/tmp/back.pdf cat A1 B1 output ' + outputFileName);
        const output = fs.readFileSync(outputFileName);
        const s3 = new AWS.S3();
        const fileName = "postalk-" + uuidv1() + '.pdf';
        await s3.putObject({
            ACL: "public-read",
            Bucket: SAVE_BUCKET_NAME,
            Key: fileName,
            Body: output
        }).promise();

        return callback(null, {
            "statusCode": 200,
            "body": JSON.stringify({
                result: 'OK',
                link: "https://s3.amazonaws.com/" + SAVE_BUCKET_NAME + "/" + fileName,
            }),
            "isBase64Encoded": false
        });
    } catch (err) {
        console.error(err);

        return callback(null, {
            "statusCode": 400,
            "body": JSON.stringify({
                result: 'ERROR',
            }),
            "isBase64Encoded": false
        });
    } finally {
        if (page) {
            await page.close();
        }

        if (browser) {
            await browser.disconnect();
        }

        if (slsChrome) {
            await slsChrome.kill();
        }
    }
};
