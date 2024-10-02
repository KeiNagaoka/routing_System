document.getElementById('number_spot').addEventListener('input', function() {
    console.log('number_spot');
    const spotNum = this.value;

    // POSTリクエストを送信する
    fetch('/routesearch/change_spot_num/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // CSRFトークンを動的に取得
        },
        body: JSON.stringify({ spot_num: spotNum }) // 送信データ
    })
    .then(response => response.json()) // レスポンスをJSONとして処理
    .then(data => {
        console.log(data); // サーバーからのデータを確認 (後で必要な処理を追加)
    })
    .catch(error => console.error('Error:', error)); // エラーハンドリング
});
