package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.CitationDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class RagClient {
  private static final Logger log = LoggerFactory.getLogger(RagClient.class);

  public enum Intent {
    KNOWLEDGE,
    ADVICE
  }

  public static class RagUnavailableException extends RuntimeException {
    public RagUnavailableException(String msg, Throwable cause) {
      super(msg, cause);
    }
  }

  public record RagResult(String answer, List<CitationDTO> citations) {}

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final String baseUrl;

  @Autowired
  public RagClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
    this(
        restTemplate,
        objectMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  public RagClient(RestTemplate restTemplate, ObjectMapper objectMapper, String baseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.baseUrl = baseUrl;
  }

  public RagResult askRag(UserDTO user, String message) {
    Map<String, Object> body = new HashMap<>();
    body.put("user_message", message);
    if (user != null) {
      Map<String, Object> ctx = new HashMap<>();
      ctx.put("nickname", user.getNickname());
      ctx.put("grade", String.valueOf(user.getGrade()));
      ctx.put(
          "preferred_position",
          user.getPreferredPosition() != null ? user.getPreferredPosition().toString() : null);
      body.put("user_context", ctx);
    }

    try {
      String json = restTemplate.postForObject(baseUrl + "/chat/rag", body, String.class);
      JsonNode root = objectMapper.readTree(json);
      String answer = root.path("answer").asText("");
      List<CitationDTO> citations = parseCitations(root.path("citations"));
      return new RagResult(answer, citations);
    } catch (Exception e) {
      log.warn("RAG 호출 실패: {}", e.getMessage());
      throw new RagUnavailableException("RAG 서비스 호출 실패", e);
    }
  }

  public Intent classify(String message) {
    Map<String, Object> body = Map.of("user_message", message);
    try {
      String json = restTemplate.postForObject(baseUrl + "/router/classify", body, String.class);
      JsonNode root = objectMapper.readTree(json);
      String intent = root.path("intent").asText("ADVICE");
      return "KNOWLEDGE".equals(intent) ? Intent.KNOWLEDGE : Intent.ADVICE;
    } catch (Exception e) {
      log.warn("Router classify 호출 실패: {}", e.getMessage());
      throw new RagUnavailableException("라우터 분류기 호출 실패", e);
    }
  }

  private List<CitationDTO> parseCitations(JsonNode arr) {
    List<CitationDTO> out = new ArrayList<>();
    if (arr == null || !arr.isArray()) return out;
    for (JsonNode n : arr) {
      CitationDTO c = new CitationDTO();
      c.setSource(n.path("source").asText(""));
      c.setSection(n.path("section").asText(""));
      if (n.hasNonNull("page")) c.setPage(n.get("page").asInt());
      c.setSnippet(n.path("snippet").asText(""));
      c.setScore(n.path("score").asDouble(0.0));
      out.add(c);
    }
    return out;
  }
}
