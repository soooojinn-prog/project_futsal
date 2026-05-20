package io.github.wizwix.letsfutsal.ai;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class PoseControllerTest {

  private MockMvc mockMvc;
  private PoseService poseService;
  private MockHttpSession session;

  @BeforeEach
  void setUp() {
    poseService = mock(PoseService.class);
    mockMvc = MockMvcBuilders.standaloneSetup(new PoseController(poseService)).build();

    session = new MockHttpSession();
    UserDTO user = new UserDTO();
    user.setUserId(1L);
    session.setAttribute("loginUser", user);
  }

  @Test
  void analyze_returnsAnalysis() throws Exception {
    PoseAnalysisDTO dto = new PoseAnalysisDTO();
    dto.setPoseClass("INSTEP_KICK");
    dto.setConfidence(0.9);
    when(poseService.analyze(any())).thenReturn(dto);

    MockMultipartFile mp =
        new MockMultipartFile("file", "x.mp4", "video/mp4", new byte[] {0, 1});

    mockMvc
        .perform(multipart("/ai/pose/analyze").file(mp).session(session))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.pose_class").value("INSTEP_KICK"));
  }

  @Test
  void analyze_returns401WithoutLogin() throws Exception {
    MockMultipartFile mp =
        new MockMultipartFile("file", "x.mp4", "video/mp4", new byte[] {0, 1});
    mockMvc
        .perform(multipart("/ai/pose/analyze").file(mp))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void posePage_returns200() throws Exception {
    mockMvc.perform(get("/ai/pose").session(session)).andExpect(status().isOk());
  }
}
