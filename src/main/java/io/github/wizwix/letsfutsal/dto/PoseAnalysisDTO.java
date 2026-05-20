package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class PoseAnalysisDTO {
  @JsonProperty("pose_class")
  private String poseClass;

  @JsonProperty("class_name")
  private String className;

  private double confidence;

  @JsonProperty("class_probabilities")
  private Map<String, Double> classProbabilities;

  @JsonProperty("key_angles")
  private KeyAnglesDTO keyAngles;

  private String feedback;

  @JsonProperty("timing_ms")
  private TimingMsDTO timingMs;

  public String getPoseClass() {
    return poseClass;
  }

  public void setPoseClass(String v) {
    this.poseClass = v;
  }

  public String getClassName() {
    return className;
  }

  public void setClassName(String v) {
    this.className = v;
  }

  public double getConfidence() {
    return confidence;
  }

  public void setConfidence(double v) {
    this.confidence = v;
  }

  public Map<String, Double> getClassProbabilities() {
    return classProbabilities;
  }

  public void setClassProbabilities(Map<String, Double> v) {
    this.classProbabilities = v;
  }

  public KeyAnglesDTO getKeyAngles() {
    return keyAngles;
  }

  public void setKeyAngles(KeyAnglesDTO v) {
    this.keyAngles = v;
  }

  public String getFeedback() {
    return feedback;
  }

  public void setFeedback(String v) {
    this.feedback = v;
  }

  public TimingMsDTO getTimingMs() {
    return timingMs;
  }

  public void setTimingMs(TimingMsDTO v) {
    this.timingMs = v;
  }
}
