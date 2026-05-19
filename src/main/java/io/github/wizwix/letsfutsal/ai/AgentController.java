package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.AgentRequestDTO;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@RequestMapping("/ai")
public class AgentController {
  private final AgentService agentService;

  public AgentController(AgentService agentService) {
    this.agentService = agentService;
  }

  @GetMapping("/coordinator")
  public String page() {
    return "ai/coordinator";
  }

  @PostMapping("/agent/run")
  @ResponseBody
  public ResponseEntity<?> run(@RequestBody AgentRequestDTO req, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    if (req.getUserInput() == null || req.getUserInput().isBlank()) {
      return ResponseEntity.badRequest().body(Map.of("error", "요청 내용을 입력해주세요."));
    }
    ProposalDTO p = agentService.run(user.getUserId(), req.getUserInput());
    return ResponseEntity.ok(p);
  }

  @PostMapping("/agent/confirm")
  @ResponseBody
  public ResponseEntity<?> confirm(
      @RequestBody ConfirmRequestDTO req, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    List<Long> ids = agentService.confirm(req, user.getUserId());
    return ResponseEntity.ok(Map.of("createdMatchIds", ids));
  }
}
