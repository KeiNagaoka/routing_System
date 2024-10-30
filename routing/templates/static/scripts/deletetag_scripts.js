// spotが変更されたときtagを変更
function updateTagOptions() {
    const spot = document.getElementById('spot').value;
    
    // フェッチAPIを使って、選択されたspotに対応するtagのリストを取得
    return fetch(`/get_spot_tag/?spot=${spot}`)
        .then(response => response.json())
        .then(data => {
            const tag = document.getElementById('tag');
            tag.innerHTML = ''; // 現在のオプションをクリア
            
            data.spot_tags.forEach(optionValue => {
                const option = document.createElement('option');
                option.value = optionValue;
                option.text = optionValue;
                tag.add(option);
            });
        })
        .catch(error => console.error('Error:', error));
}
