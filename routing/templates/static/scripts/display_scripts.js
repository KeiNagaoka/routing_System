// display_scripts.js
document.addEventListener('DOMContentLoaded', function () {
    console.log('display_scripts.js loaded');
    const showTooltipButtons = document.querySelectorAll('.show-tooltip-btn');
    const tooltips = document.querySelectorAll('.tooltip');

    showTooltipButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            console.log('show-tooltip-btn clicked');
            event.stopPropagation(); // ボタンクリック時に親要素へのイベント伝播を防ぐ

            // 全ての吹き出しを非表示にする
            tooltips.forEach(tooltip => {
                tooltip.style.display = 'none';
            });

            // クリックされたボタンに対応する吹き出しを表示する
            const spotId = this.getAttribute('data-spot-id');
            const tooltip = document.getElementById(`tooltip-${spotId}`);
            console.log(`spotId-${spotId}`);
            console.log(`tooltip-${tooltip}`);
            if (tooltip) {
                tooltip.style.display = 'block';
            }
        });
    });

    // // ドキュメントの他の部分がクリックされたときに吹き出しを非表示にする
    // document.addEventListener('click', function () {
    //     tooltips.forEach(tooltip => {
    //         tooltip.style.display = 'none';
    //     });
    // });
});

// // タグの更新
// document.addEventListener('DOMContentLoaded', function() {
//     const forms = document.querySelectorAll('form[id^="update-tag-form-"]');
//     forms.forEach(function(form) {
//         form.addEventListener('submit', function(event) {
//             event.preventDefault(); // フォームのデフォルトの送信を防ぐ

//             const formData = new FormData(this);
//             const csrfToken = formData.get('csrfmiddlewaretoken');

//             fetch(this.action, {
//                 method: 'POST',
//                 headers: {
//                     'X-CSRFToken': csrfToken,
//                     'Accept': 'application/json',
//                     'Content-Type': 'application/json'
//                 },
//                 body: JSON.stringify(Object.fromEntries(formData))
//             })
//             .then(response => response.json())
//             .then(data => {
//                 // 成功時の処理
//                 console.log('Success:', data);
//                 alert('タグが正常に追加されました。');
//             })
//             .catch(error => {
//                 // エラー時の処理
//                 console.error('Error:', error);
//                 alert('タグの追加に失敗しました。');
//             });
//         });
//     });
// });