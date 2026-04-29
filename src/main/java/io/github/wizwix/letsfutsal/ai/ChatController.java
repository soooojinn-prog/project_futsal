package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.ChatRequestDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/ai")
public class ChatController {
  private static final int DAILY_LIMIT = 30;
  private static final String COUNT_KEY = "aiChatCount";
  private static final String DATE_KEY = "aiChatDate";

  private final AiService aiService;

  public ChatController(AiService aiService) {
    this.aiService = aiService;
  }

  @PostMapping("/chat")
  public ResponseEntity<Map<String, String>> chat(
      @RequestBody ChatRequestDTO req,
      HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    if (req.getMessage() == null || req.getMessage().isBlank()) {
      return ResponseEntity.badRequest().body(Map.of("error", "메시지를 입력해주세요."));
    }
    if (isRateLimited(session)) {
      return ResponseEntity.status(429).body(Map.of("error", "오늘 사용 한도(30회)에 도달했습니다."));
    }

    String response = aiService.chat(user, req.getMessage(), List.of());
    incrementCount(session);
    return ResponseEntity.ok(Map.of("message", response));
  }

  private boolean isRateLimited(HttpSession session) {
    String today = LocalDate.now().toString();
    if (!today.equals(session.getAttribute(DATE_KEY))) {
      session.setAttribute(DATE_KEY, today);
      session.setAttribute(COUNT_KEY, 0);
    }
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    return count != null && count >= DAILY_LIMIT;
  }

  private void incrementCount(HttpSession session) {
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    session.setAttribute(COUNT_KEY, count == null ? 1 : count + 1);
  }
}
