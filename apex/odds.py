def american_to_implied(o):
    o=float(o)
    if o==0: raise ValueError("odds cannot be zero")
    return 100/(o+100) if o>0 else (-o)/((-o)+100)

def no_vig_two_way(a,b):
    pa,pb=american_to_implied(a),american_to_implied(b)
    s=pa+pb
    return pa/s,pb/s

def profit_per_unit(o):
    o=float(o)
    return o/100 if o>0 else 100/abs(o)

def fair_american(p):
    p=max(.001,min(.999,float(p)))
    return round(-100*p/(1-p)) if p>=.5 else round(100*(1-p)/p)
