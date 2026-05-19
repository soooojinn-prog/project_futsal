package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;

class IntentRouterTest {

  @Test
  void keywordMatch_routesToKnowledge_directly() {
    RagClient rag = mock(RagClient.class);
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("오프사이드 규칙이 뭐야?");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    assertThat(d.keywordHit()).isTrue();
    verifyNoInteractions(rag);
  }

  @Test
  void keywordMiss_callsClassifier_andReturnsItsAnswer() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenReturn(RagClient.Intent.ADVICE);
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("우리 팀이 자꾸 지는데");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.ADVICE);
    assertThat(d.keywordHit()).isFalse();
    verify(rag).classify("우리 팀이 자꾸 지는데");
  }

  @Test
  void classifier_failure_fallsBackToAdvice() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenThrow(new RagClient.RagUnavailableException("down", null));
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("애매한 질문");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.ADVICE);
    assertThat(d.keywordHit()).isFalse();
  }

  @Test
  void multipleKeywords_match() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenReturn(RagClient.Intent.ADVICE);
    IntentRouter router = new IntentRouter(rag);

    assertThat(router.route("4-0 포메이션 알려줘").intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    assertThat(router.route("드리블 훈련법은?").intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    // "오늘 날씨 어때"는 모든 키워드 미스 → 분류기 호출 → 위 stub으로 ADVICE 반환
    assertThat(router.route("오늘 날씨 어때").intent()).isEqualTo(RagClient.Intent.ADVICE);
  }

  @Test
  void nullMessage_returnsAdvice() {
    RagClient rag = mock(RagClient.class);
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route(null);

    assertThat(d.intent()).isEqualTo(RagClient.Intent.ADVICE);
    verifyNoInteractions(rag);
  }
}
