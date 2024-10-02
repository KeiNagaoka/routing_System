<?php
    // APIから座標を取得する処理（仮定）
    $coordinates = array(
        'longitude' => 139.627,
        'latitude' => 35.462
    );

    // 座標をJSON形式で返す
    echo json_encode(array('coordinates' => $coordinates));
?>
