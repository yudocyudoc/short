within;
package E0Reference
  "Public evaluator reference family ONLY. These are not hidden truths or generic composition outputs."
  partial model Base
    parameter Integer probe(min=1,max=4)=1 "1 pulse; 2 step; 3 ramp; 4 high pulse";
    parameter Real capacity(min=0.01)=100 "Physical transit throughput cap (units/hour)";
    parameter Real residence(min=0.01)=1.6 "Aggregate residence for any transit chain";
    Modelica.Blocks.Sources.Pulse pulse(amplitude=6,period=4,width=40,startTime=1);
    Modelica.Blocks.Sources.Step step(height=6,startTime=1);
    Modelica.Blocks.Sources.Ramp ramp(height=6,duration=3,startTime=1);
    Modelica.Blocks.Sources.Pulse highPulse(amplitude=14,period=4,width=40,startTime=1);
    Modelica.Blocks.Sources.RealExpression stimulus(
      y=if probe==1 then pulse.y else if probe==2 then step.y else
        if probe==3 then ramp.y else highPulse.y);
    IGCMolecules.AcceptedSource accepted;
    IGCMolecules.BoundedQueue preparation(maxThroughput=20,responseTime=0.5);
    IGCMolecules.BoundedQueue dispatch(maxThroughput=20,responseTime=0.5);
    IGCMolecules.DeliveryCounter counter;
    Real dispatchRate "Physical dispatch";
    Real deliveryRate "Physical receipt";
    Real inTransit "Aggregate physical transit stock";
    Real reportedDeliveryRate "Informational displayed receipt rate";
    Real deliveredTotal;
  equation
    connect(stimulus.y,accepted.externalRate);
    connect(accepted.outflow,preparation.arrival);
    connect(preparation.completed,dispatch.arrival);
    dispatchRate=dispatch.completed;
    deliveredTotal=counter.total;
  end Base;

  partial model NoTransit
    extends Base;
  equation
    connect(dispatch.completed,counter.arrival);
    deliveryRate=dispatch.completed;
    inTransit=0;
  end NoTransit;

  partial model OneTransit
    extends Base;
    IGCMolecules.BoundedQueue transit(maxThroughput=capacity,responseTime=residence);
  equation
    connect(dispatch.completed,transit.arrival);
    connect(transit.completed,counter.arrival);
    deliveryRate=transit.completed;
    inTransit=transit.waiting;
  end OneTransit;

  partial model TwoTransit
    extends Base;
    IGCMolecules.BoundedQueue transitA(maxThroughput=capacity,responseTime=residence/2);
    IGCMolecules.BoundedQueue transitB(maxThroughput=capacity,responseTime=residence/2);
  equation
    connect(dispatch.completed,transitA.arrival);
    connect(transitA.completed,transitB.arrival);
    connect(transitB.completed,counter.arrival);
    deliveryRate=transitB.completed;
    inTransit=transitA.waiting+transitB.waiting;
  end TwoTransit;

  model ZeroDirect
    extends NoTransit;
  equation
    reportedDeliveryRate=deliveryRate;
  end ZeroDirect;

  model ZeroFilter
    extends NoTransit;
    IGCInformationMolecules.FirstOrderReportFilter report(reportResponseTime=residence);
  equation
    connect(dispatch.completed,report.physicalArrivalRate);
    reportedDeliveryRate=report.reportedRate;
  end ZeroFilter;

  model OneDirect
    extends OneTransit;
  equation
    reportedDeliveryRate=deliveryRate;
  end OneDirect;

  model OneFilter
    extends OneTransit;
    IGCInformationMolecules.FirstOrderReportFilter report(reportResponseTime=residence);
  equation
    connect(transit.completed,report.physicalArrivalRate);
    reportedDeliveryRate=report.reportedRate;
  end OneFilter;

  model TwoDirect
    extends TwoTransit;
  equation
    reportedDeliveryRate=deliveryRate;
  end TwoDirect;

  model TwoFilter
    extends TwoTransit;
    IGCInformationMolecules.FirstOrderReportFilter report(reportResponseTime=residence);
  equation
    connect(transitB.completed,report.physicalArrivalRate);
    reportedDeliveryRate=report.reportedRate;
  end TwoFilter;

  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end E0Reference;
