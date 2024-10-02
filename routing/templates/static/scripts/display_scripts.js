// display_scripts.js
document.addEventListener('DOMContentLoaded', function () {
    const showTooltipButtons = document.querySelectorAll('.show-tooltip-btn');
    const tooltips = document.querySelectorAll('.tooltip');

    showTooltipButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.stopPropagation(); // ボタンクリック時に親要素へのイベント伝播を防ぐ

            // 全ての吹き出しを非表示にする
            tooltips.forEach(tooltip => {
                tooltip.style.display = 'none';
            });

            // クリックされたボタンに対応する吹き出しを表示する
            const spotId = this.getAttribute('data-spot-id');
            const tooltip = document.getElementById(`tooltip-${spotId}`);
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
