def next(self):
    if self.bline:
        try:
            self[0] = self.operation(self.a[0], self.b[0])
        except ZeroDivisionError:
            self[0] = float(f'nan')
    elif not self.r:
        if not self.btime:
            self[0] = self.operation(self.a[0], self.b)
        else:
            self[0] = self.operation(self.a.time(), self.b)
    else:
        self[0] = self.operation(self.a, self.b[0])


def _once_op(self, start, end):
    # cache python dictionary lookups
    dst = self.array
    srca = self.a.array
    srcb = self.b.array
    op = self.operation

    for i in range(start, end):
        try:
            dst[i] = op(srca[i], srcb[i])
        except ZeroDivisionError:
            dst[i] = float(f'nan')
