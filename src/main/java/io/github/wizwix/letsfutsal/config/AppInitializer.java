package io.github.wizwix.letsfutsal.config;

import jakarta.servlet.Filter;
import jakarta.servlet.MultipartConfigElement;
import jakarta.servlet.ServletRegistration;
import org.jspecify.annotations.NonNull;
import org.springframework.web.filter.CharacterEncodingFilter;
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;

public class AppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
  @Override
  protected Class<?>[] getRootConfigClasses() {
    return new Class<?>[] {RootConfig.class};
  }

  @Override
  protected Class<?>[] getServletConfigClasses() {
    return new Class<?>[] {WebConfig.class};
  }

  @Override
  protected String @NonNull [] getServletMappings() {
    return new String[] {"/"};
  }

  /** UTF-8 강제 — 한글 쿼리 파라미터가 깨지지 않도록 (Tomcat URI 기본 인코딩 ISO-8859-1 회피). */
  @Override
  protected Filter[] getServletFilters() {
    CharacterEncodingFilter encoding = new CharacterEncodingFilter();
    encoding.setEncoding("UTF-8");
    encoding.setForceEncoding(true);
    return new Filter[] {encoding};
  }

  /**
   * Multipart(영상 업로드) 활성화 — /ai/pose/analyze가 ERR_CONNECTION_RESET 없이 동작하려면 필수.
   * - maxFileSize 60MB (영상 최대 50MB + 여유)
   * - maxRequestSize 70MB
   * - fileSizeThreshold 1MB (이 이상은 디스크 임시 파일로 처리)
   */
  @Override
  protected void customizeRegistration(ServletRegistration.Dynamic registration) {
    long maxFileSize = 60L * 1024 * 1024;
    long maxRequestSize = 70L * 1024 * 1024;
    int fileSizeThreshold = 1 * 1024 * 1024;
    registration.setMultipartConfig(
        new MultipartConfigElement("", maxFileSize, maxRequestSize, fileSizeThreshold));
  }
}
