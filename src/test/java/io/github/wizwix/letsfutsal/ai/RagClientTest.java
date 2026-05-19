package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

class RagClientTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private RagClient client;
  private UserDTO user;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    client = new RagClient(restTemplate, new ObjectMapper(), "http://fake-ai:8000");
    user = new UserDTO();
    user.setNickname("수진");
    user.setGrade(1);
  }

  @Test
  void askRag_parsesAnswerAndCitations() {
    String json =
        """
        {
          "answer": "풋살에 오프사이드 없음",
          "citations": [
            {"source":"FIFA","section":"Law 11","page":14,"snippet":"no offside","score":0.9}
          ],
          "retrieved_chunks": 1
        }
        """;
    server
        .expect(requestTo("http://fake-ai:8000/chat/rag"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    RagClient.RagResult result = client.askRag(user, "오프사이드?");

    assertThat(result.answer()).isEqualTo("풋살에 오프사이드 없음");
    assertThat(result.citations()).hasSize(1);
    assertThat(result.citations().get(0).getSource()).isEqualTo("FIFA");
    assertThat(result.citations().get(0).getPage()).isEqualTo(14);
    server.verify();
  }

  @Test
  void askRag_throwsOnServerError() {
    server.expect(requestTo("http://fake-ai:8000/chat/rag")).andRespond(withServerError());

    assertThatThrownBy(() -> client.askRag(user, "질문"))
        .isInstanceOf(RagClient.RagUnavailableException.class);
  }

  @Test
  void classify_returnsIntent() {
    String json = "{\"intent\":\"KNOWLEDGE\",\"confidence\":0.92}";
    server
        .expect(requestTo("http://fake-ai:8000/router/classify"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    RagClient.Intent intent = client.classify("4-0 포메이션?");

    assertThat(intent).isEqualTo(RagClient.Intent.KNOWLEDGE);
    server.verify();
  }

  @Test
  void classify_throwsOnServerError() {
    server.expect(requestTo("http://fake-ai:8000/router/classify")).andRespond(withServerError());

    assertThatThrownBy(() -> client.classify("질문")).isInstanceOf(RagClient.RagUnavailableException.class);
  }
}
