// 経路保存ボタンが押されたときのイベント
document.addEventListener('DOMContentLoaded', function() {
    const saveRouteForms = document.querySelectorAll('.save-route-form');
    saveRouteForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();  // フォームのデフォルトの送信を防ぐ

            const formData = new FormData(this);
            const csrfToken = formData.get('csrfmiddlewaretoken');
            const route_name = formData.get('route_name');

            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById(`route-message-${route_name}`).innerText = data.message;  // メッセージを表示
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});


function ChangeSpotNum() {
    // 現在の経由地点数を取得
    const numberSpotInput = document.getElementById("number_spot");
    const currentCount = parseInt(numberSpotInput.value, 10);
    console.log(`numberSpotInput:${numberSpotInput} currentCount:${currentCount}`);

    // 1から10の範囲で表示・非表示を制御
    for (let i = 1; i < 11; i++) {
        const spotGroup = document.getElementById(`via-container${i}`);
        if (i <= currentCount) {
            spotGroup.classList.remove('hide'); // 表示
        } else {
            spotGroup.classList.add('hide'); // 非表示
        }
    }
}


// テキスト入力にする
function ChangeTextForm(idx) {
    console.log(`ChangeTextForm idx:${idx}`);
    const textSpotElement = document.getElementById(`text-spot${idx}`);
    const textSpotTarget = document.getElementById(`spot${idx}`);
    const selectSpotTarget = document.getElementById(`spot${idx}-select`);

    // selectフォームをhide
    if (textSpotElement) {
        console.log(`textSpotElement:${textSpotElement.classList}`);
        textSpotElement.classList.remove('hide');
    }
    const selectTagElement = document.getElementById(`selec-tag${idx}`);
    if (selectTagElement) {
        selectTagElement.classList.add('hide');
    }

    // POSTデータを変更
    if (textSpotTarget) {
        textSpotTarget.name = `spot${idx}`;
    }
    if (selectSpotTarget) {
        selectSpotTarget.name = `spot${idx}-hide`;
    }

}

// 選択入力にする
function ChangeSelectForm(idx) {
    console.log(`ChangeSelectForm idx:${idx}`);
    // セレクトタグの要素を非表示にする
    const selectTagElement = document.getElementById(`selec-tag${idx}`);
    const textSpotTarget = document.getElementById(`spot${idx}`);
    const selectSpotTarget = document.getElementById(`spot${idx}-select`);

    // textフォームをhide
    if (selectTagElement) {
        selectTagElement.classList.remove('hide');
    }
    const textSpotElement = document.getElementById(`text-spot${idx}`);
    if (textSpotElement) {
        textSpotElement.classList.add('hide');
    }

    
    // POSTデータを変更
    if (textSpotTarget) {
        textSpotTarget.name = `spot${idx}-hide`;
    }
    if (selectSpotTarget) {
        selectSpotTarget.name = `spot${idx}`;
    }
}

// 外部APIからデータを取得してリストにセットする関数
async function fetchSpotList(end_point) {
    try {
        const response = await fetch(`/${end_point}/`);
        const data = await response.json();
        console.log(data);

        return data.all_spot;
    } catch (error) {
        console.error('Error fetching spot list:', error);
        return [];
    }
}

// サジェスト機能を開始する関数
async function startSuggest() {
    console.log(`startSuggest`);
    const spot_tag_list = await fetchSpotList('all_spot'); // APIからデータを取得
    const spot_list = await fetchSpotList('all_spot_only'); // APIからデータを取得

    // 複数の入力フィールドに対してサジェスト機能を適用
    for (let i = 1; i < 10; i++) {
        new Suggest.Local(
            `spot${i}`,    // 入力フィールドのID
            `suggest${i}`, // サジェスト表示エリアのID
            spot_tag_list,          // サジェスト候補のリスト
            {
                dispMax: 0,
                interval: 500,
                ignoreCase: false,
                highlight: true,
            }
        );
    }
    
    // 出発地点のサジェスト機能を適用
    new Suggest.Local(
        `start_spot`,    // 入力フィールドのID
        `suggest_start`, // サジェスト表示エリアのID
        spot_list,          // サジェスト候補のリスト
        {
            dispMax: 0,
            interval: 500,
            ignoreCase: false,
            highlight: true,
        }
    );
    
    // 出発地点のサジェスト機能を適用
    new Suggest.Local(
        `goal_spot`,    // 入力フィールドのID
        `suggest_goal`, // サジェスト表示エリアのID
        spot_list,          // サジェスト候補のリスト
        {
            dispMax: 0,
            interval: 500,
            ignoreCase: false,
            highlight: true,
        }
    );
}

window.addEventListener ?
  window.addEventListener('load', startSuggest, false) :
  window.attachEvent('onload', startSuggest);
