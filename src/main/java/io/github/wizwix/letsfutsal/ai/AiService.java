package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.List;

@Service
public class AiService {
  private static final Logger log = LoggerFactory.getLogger(AiService.class);
  private static final String CLAUDE_API_URL = "https://api.anthropic.com/v1/messages";
  private static final int MAX_MESSAGE_LENGTH = 500;

  private final HttpClient httpClient = HttpClient.newHttpClient();
  private final ObjectMapper objectMapper;
  private final String apiKey;

  public AiService(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
    String raw = System.getenv("CLAUDE_API_KEY");
    this.apiKey = (raw != null) ? raw.trim() : null;
    if (this.apiKey == null || this.apiKey.isBlank()) {
      log.warn("CLAUDE_API_KEY 환경변수가 설정되지 않았습니다. 챗봇 기능이 비활성화됩니다.");
    } else {
      log.info("CLAUDE_API_KEY 로드 완료 (길이: {}자)", this.apiKey.length());
    }
  }

  public String chat(UserDTO user, String rawMessage, List<MatchDTO> recentMatches) {
    if (apiKey == null || apiKey.isBlank()) {
      return "AI 서비스가 설정되지 않았습니다. (서버에 API 키가 없습니다)";
    }

    String message = rawMessage.length() > MAX_MESSAGE_LENGTH
        ? rawMessage.substring(0, MAX_MESSAGE_LENGTH)
        : rawMessage;
    message = HtmlUtils.htmlEscape(message);

    try {
      String requestBody = buildRequestBody(buildSystemPrompt(user, recentMatches), message);
      HttpRequest request = HttpRequest.newBuilder()
          .uri(URI.create(CLAUDE_API_URL))
          .header("Content-Type", "application/json")
          .header("x-api-key", apiKey)
          .header("anthropic-version", "2023-06-01")
          .POST(HttpRequest.BodyPublishers.ofString(requestBody))
          .build();

      HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      log.info("Claude API 응답 상태코드: {}", response.statusCode());
      if (response.statusCode() != 200) {
        log.error("Claude API 오류 응답: {}", response.body());
        return parseErrorResponse(response.body());
      }
      return parseResponse(response.body());
    } catch (Exception e) {
      log.error("Claude API 호출 중 예외 발생: {} - {}", e.getClass().getSimpleName(), e.getMessage(), e);
      return "AI 서비스 오류: " + e.getClass().getSimpleName() + " - " + e.getMessage();
    }
  }

  private String buildSystemPrompt(UserDTO user, List<MatchDTO> recentMatches) {
    StringBuilder sb = new StringBuilder();
    sb.append("당신은 풋살 전문 AI 어시스턴트입니다.\n");
    sb.append("현재 유저 정보:\n");
    sb.append("- 닉네임: ").append(user.getNickname()).append("\n");
    sb.append("- 선호 포지션: ").append(
        user.getPreferredPosition() != null ? user.getPreferredPosition() : "없음").append("\n");
    sb.append("- 실력 등급: ").append(user.getGrade()).append("\n");
    if (recentMatches != null && !recentMatches.isEmpty()) {
      sb.append("- 최근 매치: ");
      recentMatches.stream().limit(3).forEach(m ->
          sb.append(m.getMatchDate()).append(" ").append(m.getRegion()).append(" | "));
    }
    sb.append("\n이 정보를 바탕으로 개인화된 풋살 조언을 제공하세요. ");
    sb.append("풋살과 무관한 질문은 정중히 거절하세요.");
    return sb.toString();
  }

  private String buildRequestBody(String systemPrompt, String userMessage) throws Exception {
    String systemJson = objectMapper.writeValueAsString(systemPrompt);
    String messageJson = objectMapper.writeValueAsString(userMessage);
    return String.format(
        "{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":2048,\"system\":%s,\"messages\":[{\"role\":\"user\",\"content\":%s}]}",
        systemJson, messageJson);
  }

  private String parseResponse(String responseBody) throws Exception {
    var root = objectMapper.readTree(responseBody);
    var content = root.path("content");
    if (content.isArray() && content.size() > 0) {
      return content.get(0).path("text").asText("응답 텍스트를 읽을 수 없습니다.");
    }
    log.error("Claude API 응답에 content 배열 없음: {}", responseBody);
    return "잠시 후 다시 시도해주세요.";
  }

  private String parseErrorResponse(String responseBody) {
    try {
      var root = objectMapper.readTree(responseBody);
      String errorType = root.path("error").path("type").asText("unknown");
      String errorMsg = root.path("error").path("message").asText("알 수 없는 오류");
      return "AI 오류 [" + errorType + "]: " + errorMsg;
    } catch (Exception ex) {
      return "AI 서비스 오류가 발생했습니다.";
    }
  }
}
