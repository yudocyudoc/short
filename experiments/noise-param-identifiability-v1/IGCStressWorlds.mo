within;
package IGCStressWorlds
  "Held-out parameter worlds. Parameters are not supplied to the discriminator."
  model FastDirect
    extends IGCObservationGraphs.Direct(preparationResponseTime=0.4,dispatchResponseTime=0.35);
  end FastDirect;
  model FastTransitOnly
    extends IGCObservationGraphs.TransitOnly(preparationResponseTime=0.4,dispatchResponseTime=0.35,transitResponseTime=0.35);
  end FastTransitOnly;
  model FastReportOnly
    extends IGCObservationGraphs.ReportOnly(preparationResponseTime=0.4,dispatchResponseTime=0.35,reporter(reportResponseTime=0.18));
  end FastReportOnly;
  model FastTransitAndReport
    extends IGCObservationGraphs.TransitAndReport(preparationResponseTime=0.4,dispatchResponseTime=0.35,transitResponseTime=0.35,reporter(reportResponseTime=0.18));
  end FastTransitAndReport;
  model SlowDirect
    extends IGCObservationGraphs.Direct(preparationResponseTime=0.9,dispatchResponseTime=0.7);
  end SlowDirect;
  model SlowTransitOnly
    extends IGCObservationGraphs.TransitOnly(preparationResponseTime=0.9,dispatchResponseTime=0.7,transitResponseTime=3.0);
  end SlowTransitOnly;
  model SlowReportOnly
    extends IGCObservationGraphs.ReportOnly(preparationResponseTime=0.9,dispatchResponseTime=0.7,reporter(reportResponseTime=2.3));
  end SlowReportOnly;
  model SlowTransitAndReport
    extends IGCObservationGraphs.TransitAndReport(preparationResponseTime=0.9,dispatchResponseTime=0.7,transitResponseTime=3.0,reporter(reportResponseTime=2.3));
  end SlowTransitAndReport;
  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCStressWorlds;
