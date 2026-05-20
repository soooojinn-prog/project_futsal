package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.multipart.MultipartFile;

@Controller
@RequestMapping("/ai")
public class PoseController {

  private static final int DAILY_LIMIT = 10;
  private static final String COUNT_KEY = "poseAnalyzeCount";
  private static final String DATE_KEY = "poseAnalyzeDate";

  private final PoseService poseService;

  public PoseController(PoseService poseService) {
    this.poseService = poseService;
  }

  @GetMapping("/pose")
  public String page() {
    return "ai/pose";
  }

  @PostMapping("/pose/analyze")
  @ResponseBody
  public ResponseEntity<?> analyze(
      @RequestParam("file") MultipartFile file, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요해요."));
    }
    if (file.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("error", "영상을 업로드해 주세요."));
    }
    if (file.getSize() > 50L * 1024 * 1024) {
      return ResponseEntity.badRequest()
          .body(Map.of("error", "영상은 최대 50MB까지 가능해요."));
    }
    if (isRateLimited(session)) {
      return ResponseEntity.status(429)
          .body(Map.of("error", "오늘 사용 한도(10회)에 도달했어요."));
    }
    PoseAnalysisDTO dto = poseService.analyze(file);
    incrementCount(session);
    return ResponseEntity.ok(dto);
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
