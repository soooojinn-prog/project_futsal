package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

class PoseServiceTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private PoseService service;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    service = new PoseService(restTemplate, new ObjectMapper(), "http://fake:8000");
  }

  @Test
  void analyze_parsesResponse() throws Exception {
    String json =
        "{\"pose_class\":\"INSTEP_KICK\",\"class_name\":\"인스텝킥\","
            + "\"confidence\":0.87,"
            + "\"class_probabilities\":{\"INSIDE_KICK\":0.05,\"INSTEP_KICK\":0.87,"
            + "\"INFRONT_KICK\":0.08},"
            + "\"key_angles\":{"
            + "\"left_knee\":{\"mean\":168,\"min\":158,\"max\":175},"
            + "\"right_knee\":{\"mean\":145,\"min\":130,\"max\":160},"
            + "\"left_ankle\":{\"mean\":90,\"min\":82,\"max\":100},"
            + "\"right_ankle\":{\"mean\":92,\"min\":85,\"max\":99}},"
            + "\"feedback\":\"무릎이 너무 펴졌어요.\","
            + "\"timing_ms\":{\"frame_extract\":420,\"mediapipe\":1850,"
            + "\"classify\":12,\"feedback\":1200,\"total\":3500}}";
    server
        .expect(requestTo("http://fake:8000/pose/analyze"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    MockMultipartFile mp =
        new MockMultipartFile("file", "test.mp4", "video/mp4", new byte[] {0, 1, 2});
    PoseAnalysisDTO dto = service.analyze(mp);

    assertThat(dto.getPoseClass()).isEqualTo("INSTEP_KICK");
    assertThat(dto.getConfidence()).isEqualTo(0.87);
    assertThat(dto.getKeyAngles().getLeftKnee().getMean()).isEqualTo(168);
    assertThat(dto.getTimingMs().getTotal()).isEqualTo(3500);
  }
}
