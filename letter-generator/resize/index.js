const im = require('imagemagick');
const aws = require('aws-sdk');
const s3 = new aws.S3({
    apiVersion: '2006-03-01'
});

// This function refers to https://beyondjapan.com/blog/2017/04/lambda-image-auto-resize
exports.handler = (event, context, callback) => {
    const bucket = event.Records[0].s3.bucket.name;
    const key = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
    const params = {
        Bucket: bucket,
        Key: key,
    };
    s3.getObject(params, (err, data) => {
        if (err) {
            console.log(err);
            const message = `Error getting object ${key} from bucket ${bucket}. Make sure they exist and your bucket is in the same region as this function.`;
            console.log(message);
            callback(message);
        } else {
            const contentType = data.ContentType;
            const extension = key.split('.').pop();
            if (!["jpeg", "jpg"].includes(extension)) {
                console.log(key + " is not jpg, return");
                return;
            }
            console.log(key + " is jpg, continue");

            im.resize({
                srcData: data.Body,
                format: extension,
                width: 100
            }, function (err, stdout, stderr) {
                if (err) {
                    context.done('resize failed', err);
                } else {
                    s3.putObject({
                        ACL: "public-read",
                        Bucket: bucket + ".resize",
                        Key: key.split('.')[0] + "-thumbnail." + extension,
                        Body: new Buffer(stdout, 'binary'),
                        ContentType: contentType
                    }, function (err, res) {
                        if (err) {
                            context.done('error putting object', err);
                        } else {
                            callback(null, "success putting object");
                        }
                    });
                }
            });

            im.resize({
                srcData: data.Body,
                format: extension,
                width: 500
            }, function (err, stdout, stderr) {
                if (err) {
                    context.done('resize failed', err);
                } else {
                    s3.putObject({
                        ACL: "public-read",
                        Bucket: bucket + ".resize",
                        Key: key.split('.')[0] + "-preview." + extension,
                        Body: new Buffer(stdout, 'binary'),
                        ContentType: contentType
                    }, function (err, res) {
                        if (err) {
                            context.done('error putting object', err);
                        } else {
                            callback(null, "success putting object");
                        }
                    });
                }
            });
        }
    });
};
