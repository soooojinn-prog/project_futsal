package io.github.wizwix.letsfutsal.ai;

import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class IntentRouter {
  private static final Logger log = LoggerFactory.getLogger(IntentRouter.class);

  private static final Set<String> KNOWLEDGE_KEYWORDS =
      Set.of(
          "규칙", "반칙", "오프사이드", "파울", "프리킥", "페널티킥", "킥인", "코너킥",
          "포메이션", "4-0", "3-1", "2-2", "전술", "압박", "카운터",
          "드리블", "패스", "슈팅", "트래핑", "훈련", "연습");

  public record Decision(RagClient.Intent intent, boolean keywordHit) {}

  private final RagClient ragClient;

  public IntentRouter(RagClient ragClient) {
    this.ragClient = ragClient;
  }

  public Decision route(String message) {
    if (message == null) {
      return new Decision(RagClient.Intent.ADVICE, false);
    }
    String normalized = message.toLowerCase();
    for (String kw : KNOWLEDGE_KEYWORDS) {
      if (normalized.contains(kw.toLowerCase())) {
        log.info("Routing: keyword HIT '{}' → KNOWLEDGE", kw);
        return new Decision(RagClient.Intent.KNOWLEDGE, true);
      }
    }
    try {
      RagClient.Intent intent = ragClient.classify(message);
      log.info("Routing: keyword MISS, LLM classifier → {}", intent);
      return new Decision(intent, false);
    } catch (RagClient.RagUnavailableException e) {
      log.warn("Routing: classifier 실패, ADVICE로 폴백");
      return new Decision(RagClient.Intent.ADVICE, false);
    }
  }
}
