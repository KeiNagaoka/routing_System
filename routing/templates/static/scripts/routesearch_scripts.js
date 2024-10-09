// document.getElementById('number_spot').addEventListener('input', function() {
//     console.log('number_spot');
//     const spotNum = this.value;

//     // POSTリクエストを送信する
//     fetch('/routesearch/change_spot_num/', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//             'X-CSRFToken': getCookie('csrftoken') // CSRFトークンを動的に取得
//         },
//         body: JSON.stringify({ spot_num: spotNum }) // 送信データ
//     })
//     .then(response => response.json()) // レスポンスをJSONとして処理
//     .then(data => {
//         console.log(data); // サーバーからのデータを確認 (後で必要な処理を追加)
//     })
//     .catch(error => console.error('Error:', error)); // エラーハンドリング
// });


function ChangeSpotNum() {
    // spots_containerを取得
    const container = document.getElementById('spots_container');
    
    // 現在の内容をクリア
    container.innerHTML = '';

    // number_spotの値を取得
    const numberOfSpots = parseInt(document.getElementById('number_spot').value);

    // 指定された数だけform-groupを生成
    for (let i = 1; i <= numberOfSpots; i++) {
        container.innerHTML += `
            <div class="form-group">
                <label for="spot${i}">経由地点${i}:</label>
                <select id="spot${i}" name="spot${i}">
                    <option value="セブンイレブン">セブンイレブン</option>
                    <option value="ファミリーマート">ファミリーマート</option>
                    <option value="ローソン">ローソン</option>
                    <option value="レストラン">レストラン</option>
                    <option value="駅">駅</option>
                </select>
                
                <label for="number${i}">箇所数${i}:</label>
                <input type="number" id="number${i}" name="number${i}" min="1" value="1">
            </div>
        `;
    }
}
