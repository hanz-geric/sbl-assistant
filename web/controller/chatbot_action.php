<?php
    include __DIR__ . '/../config/dbconn.php';
    include __DIR__ . '/../model/chatbot.php';

    session_start();
    $sessionId = session_id();
    session_write_close();

    set_time_limit(180);

    $chatbot = new Chatbot($pdo);

    if (isset($_GET['action']) && $_GET['action'] == 'get') {
        $messages = $chatbot->getMessages($sessionId);

        foreach ($messages as $msg) { ?>
            <div class="<?= $msg['role'] ?>">
                <?= nl2br(htmlspecialchars($msg['content'])) ?>
                <?php if ($msg['role'] == 'bot' && !empty($msg['response_time'])) { ?>
                    <div class="sources"><?= $msg['response_time'] ?> s</div>
                <?php } ?>
            </div>
        <?php }
        exit;
    }

    if ($_SERVER['REQUEST_METHOD'] == 'POST') {
        $question = trim($_POST['question'] ?? '');
        echo json_encode($chatbot->ask($sessionId, $question));
    }
?>
