package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@Service
public class PoseService {
  private static final Logger log = LoggerFactory.getLogger(PoseService.class);

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final String aiBaseUrl;

  @Autowired
  public PoseService(RestTemplate restTemplate, ObjectMapper objectMapper) {
    this(
        restTemplate,
        objectMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  public PoseService(RestTemplate restTemplate, ObjectMapper objectMapper, String aiBaseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.aiBaseUrl = aiBaseUrl;
  }

  public PoseAnalysisDTO analyze(MultipartFile video) {
    try {
      byte[] bytes = video.getBytes();
      ByteArrayResource resource =
          new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
              return video.getOriginalFilename();
            }
          };

      MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
      body.add("file", resource);

      HttpHeaders headers = new HttpHeaders();
      headers.setContentType(MediaType.MULTIPART_FORM_DATA);

      HttpEntity<MultiValueMap<String, Object>> req = new HttpEntity<>(body, headers);
      return restTemplate.postForObject(aiBaseUrl + "/pose/analyze", req, PoseAnalysisDTO.class);
    } catch (IOException e) {
      log.warn("Pose 분석 영상 읽기 실패: {}", e.getMessage());
      throw new RuntimeException("영상 파일을 읽을 수 없습니다.", e);
    } catch (HttpStatusCodeException e) {
      // Python에서 503/400 등 의도된 상태 코드로 응답한 경우 — 상태 코드를 메시지에 보존해서
      // PoseController가 적절한 친절 메시지로 변환할 수 있게 함.
      int code = e.getStatusCode().value();
      String detail = e.getResponseBodyAsString();
      log.warn("Pose 분석 Python 응답 오류 {}: {}", code, detail);
      throw new RuntimeException("HTTP " + code + ": " + detail, e);
    } catch (Exception e) {
      log.warn("Pose 분석 호출 실패: {}", e.getMessage());
      throw new RuntimeException("자세 분석 서비스 호출 실패", e);
    }
  }
}
