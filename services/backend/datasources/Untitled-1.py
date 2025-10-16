def myFun1(in1, in2):
    x = in1
    y = in2
    out1 = 6
    out1, out2 = myFun2(x, y)
    print(f'in1={in1:.0f}, in2={in2:.0f}, out1={out1:.0f}')
    return out1
# --------------------------------------------------------
def myFun2(in2, in1):
    a = in1*3
    b = in2*2
    out1 = a+b
    out2 = a-b
    print(f'in1={in1:.0f}, in2={in2:.0f}, out1={out1:.0f}, out2={out2:.0f}')
    return out2, out1
# --------------------------------------------------------
def myFun3():
    var1 = 1
    var2 = 2
    output = 3
    print(f'var1={var1:.0f}, var2={var2:.0f}, output={output:.0f}')
    output = myFun1(var1, var2)
    print(f'var1={var1:.0f}, var2={var2:.0f}, output={output:.0f}')

# --------------------------------------------------------
var1 = 4
var2 = 2
myFun3()
print(f'var1={var1:.0f}, var2={var2:.0f}')