within;
package IGCTransitProbes
  model NoOrdersDirect
    extends IGCTransitGraphs.Direct(beforeRush=0,duringRush=0);
  end NoOrdersDirect;
  model NoOrdersBuffered
    extends IGCTransitGraphs.Buffered(beforeRush=0,duringRush=0);
  end NoOrdersBuffered;
end IGCTransitProbes;
