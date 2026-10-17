within;
package IGCObservationScenarios
  model ZeroDirect
    extends IGCObservationGraphs.Direct(beforeRush=0,duringRush=0);
  end ZeroDirect;
  model ZeroTransitOnly
    extends IGCObservationGraphs.TransitOnly(beforeRush=0,duringRush=0);
  end ZeroTransitOnly;
  model ZeroReportOnly
    extends IGCObservationGraphs.ReportOnly(beforeRush=0,duringRush=0);
  end ZeroReportOnly;
  model ZeroTransitAndReport
    extends IGCObservationGraphs.TransitAndReport(beforeRush=0,duringRush=0);
  end ZeroTransitAndReport;
end IGCObservationScenarios;
