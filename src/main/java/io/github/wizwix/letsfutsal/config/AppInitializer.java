package io.github.wizwix.letsfutsal.config;

import jakarta.servlet.Filter;
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
}
