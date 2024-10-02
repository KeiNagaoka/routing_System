document.getElementById('number_spot').addEventListener('change', function() {
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
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json(); // レスポンスをJSONとして処理
    })
    .then(data => {
        console.log(data); // サーバーからのデータを確認 (後で必要な処理を追加)
    })
    .catch(error => console.error('Error:', error)); // エラーハンドリング
});

// CSRFトークンを取得する関数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
