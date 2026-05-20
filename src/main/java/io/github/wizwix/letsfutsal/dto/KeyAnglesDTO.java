package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class KeyAnglesDTO {
  public static class AngleStats {
    private double mean;
    private double min;
    private double max;

    public double getMean() {
      return mean;
    }

    public void setMean(double mean) {
      this.mean = mean;
    }

    public double getMin() {
      return min;
    }

    public void setMin(double min) {
      this.min = min;
    }

    public double getMax() {
      return max;
    }

    public void setMax(double max) {
      this.max = max;
    }
  }

  @JsonProperty("left_knee")
  private AngleStats leftKnee;

  @JsonProperty("right_knee")
  private AngleStats rightKnee;

  @JsonProperty("left_ankle")
  private AngleStats leftAnkle;

  @JsonProperty("right_ankle")
  private AngleStats rightAnkle;

  public AngleStats getLeftKnee() {
    return leftKnee;
  }

  public void setLeftKnee(AngleStats v) {
    this.leftKnee = v;
  }

  public AngleStats getRightKnee() {
    return rightKnee;
  }

  public void setRightKnee(AngleStats v) {
    this.rightKnee = v;
  }

  public AngleStats getLeftAnkle() {
    return leftAnkle;
  }

  public void setLeftAnkle(AngleStats v) {
    this.leftAnkle = v;
  }

  public AngleStats getRightAnkle() {
    return rightAnkle;
  }

  public void setRightAnkle(AngleStats v) {
    this.rightAnkle = v;
  }
}
