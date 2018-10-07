# Models

アプリケーションに用いるデータモデルの定義を書く

## Letter

`Letter` は以下のフィールドを持つ:

| Name               | Required | Type   | Description     |
| ------------------ | -------- | ------ | --------------- |
| `id`               | true     | string | レターのID     |
| `user_id`          | true     | string | ユーザーのID   |
| `postal_code`      | true     | int    | 郵便番号        |
| `receiver_name`    | true     | string | 送り先の名前    |
| `receiver_address` | true     | string |  送り先の住所   |
| `message`          | true     | string | レターの本文    |
| `front_image`      | true     | string | 表側の画像 URL  |
| `back_image`       | true     | string | 裏側の画像 URL  |
| `created_at`       | false    | string |  レターの作成日 |

## User

`User` は以下のフィールドを持つ:

| Name           | Required | Type   | Description                                                                                                                                     |
| -------------- | -------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`           | true     | string | ユーザーの ID                                                                                                                                   |
| `line_user_id` | true     | string | [LINE ユーザープロフィール](https://developers.line.me/ja/reference/messaging-api/#anchor-221905521cf87b33d0a70f98f4e7f0c55fa2e800)の `userId` |
| `name`         | false    | string | レターの送り元の名前                                                                                                                           |
| `address`      | false    | string | レターの送り元の住所                                                                                                                           |
