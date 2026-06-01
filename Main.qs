operation Main() : Result[] {
    Message("Hello, world!");

    use (q0, q1, q2) = (Qubit(), Qubit(), Qubit());

    // Basis-state weights:
    // |000>: observe=1, |001>: cast=10, |010>: listen=100,
    // |100>: post=40, |110>: reflect=50.
    Ry(1.4661277029685484, q0);

    X(q0);
    Controlled Ry([q0], (2.5011005885653774, q1));
    X(q0);

    Controlled Ry([q0], (1.6821373411358604, q1));

    X(q0);
    X(q1);
    Controlled Ry([q0, q1], (2.5290379152504547, q2));
    X(q1);
    X(q0);

    return [MResetZ(q0), MResetZ(q1), MResetZ(q2)];
}
