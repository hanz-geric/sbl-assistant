<?php
	class Chatbot {
		private $pdo;
		private $ollamaUrl = 'http://localhost:11434';
		private $model = 'gemma3:4b';

		function __construct($pdo){
			$this->pdo = $pdo;
		}

		function saveMessage($sessionId, $role, $content, $sources = null, $responseTime = null){
			$sql = 'INSERT INTO messages(session_id, role, content, sources, response_time) VALUES(?,?,?,?,?)';
			$stmt = $this->pdo->prepare($sql);
			return $stmt->execute([$sessionId, $role, $content, $sources, $responseTime]);
		}

		function getMessages($sessionId){
			$sql = 'SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC';
			$stmt = $this->pdo->prepare($sql);
			$stmt->execute([$sessionId]);
			return $stmt->fetchAll(PDO::FETCH_ASSOC);
		}

		function callOllama($endpoint, $payload){
			$ch = curl_init($this->ollamaUrl . $endpoint);

			curl_setopt_array($ch, [
				CURLOPT_POST => true,
				CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
				CURLOPT_POSTFIELDS => json_encode($payload),
				CURLOPT_RETURNTRANSFER => true,
				CURLOPT_TIMEOUT => 120
			]);

			$result = curl_exec($ch);

			if ($result === false) {
				$error = curl_error($ch);
				curl_close($ch);
				return ['error' => $error];
			}

			curl_close($ch);
			return json_decode($result, true);
		}

		function ask($sessionId, $question){
			if (empty($question)) {
				return ['message' => 'Please type a question', 'status' => 'failed'];
			}

			$this->saveMessage($sessionId, 'user', $question);

			$start = microtime(true);

			$data = $this->callOllama('/api/chat', [
				'model' => $this->model,
				'messages' => [
					['role' => 'system', 'content' => 'You are the Small Business and Livelihood Assistant for Baguio City and Benguet, Philippines. Answer briefly in English.'],
					['role' => 'user', 'content' => $question]
				],
				'stream' => false,
				'options' => ['temperature' => 0.1]
			]);

			$time = round(microtime(true) - $start, 2);

			if (!isset($data['message']['content'])) {
				return ['message' => 'Could not get an answer from the model. ' . ($data['error'] ?? ''), 'status' => 'failed'];
			}

			$answer = trim($data['message']['content']);

			$this->saveMessage($sessionId, 'bot', $answer, null, $time);

			return ['answer' => $answer, 'time' => $time, 'status' => 'success'];
		}
	}
?>
