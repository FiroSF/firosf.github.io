---
title: "합동식과 페르마의 소정리, 백준 11401, 백준 13977"
date: 2023-09-03 00:00:00 +0900
last_modified_at: 2026-08-13 07:04:55 +0900
categories: [알고리즘, 정수론]
tags: [PS, C++, 수학, 정수론, 백준, 알고리즘]
description: "합동식과 페르마의 소정리, 연습문제 해설"
math: true
---

[원본 글(Velog)](https://velog.io/@cmgjol010/%ED%95%A9%EB%8F%99%EC%8B%9D%EA%B3%BC-%ED%8E%98%EB%A5%B4%EB%A7%88%EC%9D%98-%EC%86%8C%EC%A0%95%EB%A6%AC-%EB%B0%B1%EC%A4%80-11401)

---

페르마의 소정리를 찾으려니까 합동식이 나왔는데, 이게 뭔지를 몰라서 그냥 둘 다 같이 정리해서 적어봤다. 최대한 간결하게 적으려 했지만 뒤로 갈수록 글이 길게 적혔다. 나도 배우는 입장이라 틀린 부분이 있을 수 있다. 지적 환영

## 1. 약수 기호 |
> * $a \mid b$ ($a, b$는 정수)  
> 
> = $a$는 $b$의 약수  
> = $b$는 $a$의 배수  
> = `b % a == 0` (단, 이 경우에는 $a$가 $0$이 아닌 정수)  
> = $b = ac$를 만족하는 정수 $c$가 존재

음수도 성립하기 때문에 $-3 \mid 9$ 또한 성립한다.

## 2. 합동식이란?
> * $a \equiv b \pmod m$ ($a, b$는 정수, $m$은 양의 정수)  
> 
> = $a$와 $b$를 $m$으로 나눈 나머지가 같다  
> = `a % m == b % m`

$a$와 $b$의 나머지가 같으니 $a - b$를 $m$으로 나눈 나머지는 $0$이다. 따라서,

> * $a \equiv b \pmod m$ 는 $m \mid (a - b)$ 과 같다.

### 참고

$a \equiv b \pmod m$ 과 $a = b \bmod m$ 은 다르다. 전자는 `a % m == b % m` 이고, 후자는 `a == b % m` 이다.

$a \equiv a \pmod m$ 이 성립한다.

$a \equiv$ `a % m` $\pmod m$ 도 물론 성립한다. ($\%$는 나머지 연산, 좌측 식은 $a \equiv a \bmod m \pmod m$과 같지만 이러면 내가 헷갈려서 저렇게 적음)

## 3. 합동식의 성질

$a \equiv b \pmod m$ 이고 $c \equiv d \pmod m$ 일 때 아래 네 성질을 만족한다:

> 1 . $a \pm c \equiv b \pm d \pmod m$
>
> = `(a ± c) % m == (b ± d) % m`  
> ≒ `(a ± c) % m == ((a % m) ± (c % m)) % m`

$a$의 나머지와 $b$의 나머지가 같고, $c$의 나머지와 $d$의 나머지가 같다. $a+c$와 $b+d$의 나머지도 당연히 같을 것이다.

> 2 . $ac \equiv bd \pmod m$
>
> = `ac % m == bd % m`  
> ≒ `ac % m == ((a % m) * (c % m)) % m`

각 문자들을 $(tm + x)$의 꼴로 바꾼 뒤 계산하면 나머지가 같게 나올 것이다.

> 3 . $a^n \equiv b^n \pmod m$
>
> ≒ $aa \equiv bb \pmod m$

2번을 여러 번 계산한다.

> 4 . $m$과 $t$가 서로소인 경우, $\frac{a}{t} \equiv \frac{b}{t} \pmod m$

증명은 [이 글](https://dimenchoi.tistory.com/50)을 읽어보자. 양변 모두 정수여야 할 것이다.  
보시다시피 덧셈과 뺄셈 곱셈과 달리 나눗셈은 규칙이 다르다. 나눗셈만큼은 양변에 $c$와 $d$로 각각 나눌 수 없다.

## 4. 합동식 활용

합동식의 특징을 생각하면 $a \equiv$ `a % m` $\pmod m$임을 알 수 있다. ($\%$는 나머지 연산) 이걸로 큰 수 연산을 할 수 있다. 이걸 풀어보자.

> $7$의 $n$제곱을 $1,000,000,007$로 나눈 나머지를 구하시오. ($0 < n \le 1,000,000$, $n$은 정수)

$7$의 $n$제곱을 그냥 구하면 오버플로우가 날 것이다. 합동식을 이용해 구하면 오버플로우를 피할 수 있다.  
$m = 1,000,000,007$로 두자.  
$a \equiv a \pmod m$이므로 $7 \equiv 7 \pmod m$ 이다. 2번 성질을 이용해 여기서 양변에 $7$을 곱한 뒤 $a \equiv$ `a % m` $\pmod m$ 이므로 우변을 $m$으로 나눈 나머지로 바꿔주자. 이를 반복하면 원하는 값을 구할 수 있다.

즉, 이런 식으로 구하게 된다:

$7 \equiv 7 \pmod m$  
$7^2 \equiv$ `7 * 7 % m` $\pmod m$  
$7^3 \equiv$ `49 * 7 % m` $\pmod m$  
$7^4 \equiv$ `343 * 7 % m` $\pmod m$  
...

실제 계산할 때는 우변만 계산해 준다. C++로 구현하면 다음과 같다.

{% raw %}
```cpp
int n;
cin >> n;
long long result = 7;
for (int i = 1; i < n; i++)
{
	result *= 7;
	result %= 1000000007;
}
cout << result;
```
{% endraw %}

## 5. 페르마의 소정리

> $p$는 소수, $a$는 정수일 때
>
> * $a^p \equiv a \pmod p$

> $p$가 소수이며 $a$가 $p$의 배수가 아니면  
> 
> $a^{p-1} \equiv 1 \pmod p$

이거 증명 방법은 굉장히 다양하다. [나무위키 '페르마의 소정리'](https://namu.wiki/w/%ED%8E%98%EB%A5%B4%EB%A7%88%EC%9D%98%20%EC%86%8C%EC%A0%95%EB%A6%AC) 문서에 잘 정리되어 있다. 그 중 내게 가장 직관적으로 다가온 증명은 [이것](https://namu.wiki/w/%ED%8E%98%EB%A5%B4%EB%A7%88%EC%9D%98%20%EC%86%8C%EC%A0%95%EB%A6%AC#s-2.4)이다. 이 설명에 덧붙이자면 $p$가 소수가 아닌 경우 겹치는 경우의 수가 줄어들 수 있기 때문에 성립하지 않는다.

$p = 4, a = 3$인 경우를 생각하자. 또한, 색의 종류를 $1, 2, 3$과 같이 표현하자. 글에서 알 수 있듯이 $1221$과 $2112$, $1122$, $2211$처럼 $p$가지의 같은 목걸이가 존재한다. 그러나 $1212$와 $2121$처럼 같은 목걸이의 종류가 $p$가지가 아닌 경우가 존재하므로 위 글처럼 계산할 수 없다. 이런 경우가 생기지 않으려면 $p$가 소수여야 한다.

$a^p \equiv a \pmod p$를 구했으니, 양변을 $a$로 나누면 두 번째 식이 나온다. 단, $a$와 $p$가 서로소인 경우에만 양변을 $a$로 나눌 수 있다. 서로소가 아니면 $a$가 $p$의 배수이므로 $a^{p-1} \equiv 0 \pmod p$가 된다.

## 6. 페르마의 소정리 활용

### 나머지 연산의 곱셈 역원 구하기

> $ab \equiv 1 \pmod m$ 일 때, $b$를 $a$의 나머지 연산의 곱셈 역원이라 한다.  
> 
> `= ab % m == 1` 일 때, $b$를 $a$의 나머지 연산의 곱셈 역원이라 한다.

곱셈으로 치면 역수. 이를 활용하면 다음과 같은 식을 얻을 수 있다:

> $b$가 $a$의 나머지 연산의 곱셈 역원일 때, $\frac{x}{a} \equiv bx \pmod m$ (단, $\frac{x}{a}$는 정수)

즉, 나눗셈을 곱셈으로 바꿀 수 있다. 간단하게 $\frac{1}{a}$을 $b$로 바꿔주면 된다. 나눗셈을 곱셈으로 바꾸게 되면 합동식의 성질을 활용하기 용이하다.

이걸 구하는 방법으로는 확장 유클리드 알고리즘이 있다. 하지면 여기서는 다루지 않고, 대신 $m$이 소수일 때 페르마의 소정리를 활용해 구하는 방법을 다뤄 보겠다. 구하는 방법은 아주 간단하다.

페르마의 소정리 $a^{p-1} \equiv 1 \pmod p$에서, 식을 $a \cdot a^{p-2} \equiv 1 \pmod p$ 로 바꿔보자. 짜잔! $a$의 나머지 연산의 곱셈 역원은 $a^{p-2}$ 이다. 당연하게도, 페르마의 소정리는 $p$가 소수일 때만 성립하므로 $p$가 소수가 아닐 때는 이 방법을 쓸 수 없다. 이 경우에는 앞서 언급한 확장 유클리드 알고리즘을 사용해야 한다.

### [백준 11401](https://www.acmicpc.net/problem/11401)

> 자연수 $N$과 정수 $K$가 주어졌을 때 이항 계수 $\binom{N}{K}$를 $1,000,000,007$로 나눈 나머지를 구하는 프로그램을 작성하시오.

이 글을 쓴 목적이다.  
먼저, $$\binom{n}{r} = {}_{n}\mathrm{C}_{r}$$ 이다. 이걸 구하는 공식은 $\binom{n}{r} = \frac{n!}{r!(n-r)!}$ 이다. 팩토리얼 값은 합동식을 활용해서 $1,000,000,007$로 나눈 나머지를 구할 수 있다. 그러나 나눗셈만큼은 합동식의 성질만을 활용해서 구할 수 없다. 이 때 페르마의 소정리를 활용한다.

먼저 구하는 식은 다음과 같다. $p$는 $1,000,000,007$이다.

$$\frac{n!}{r!(n-r)!} \bmod p$$

나눗셈이 나왔다. 나눗셈은 앞서 구한 나머지 연산의 곱셈 역원을 이용해 곱셈으로 바꿔주자. 그럼 다음과 같은 식이 나온다:

$$n!(r!(n-r)!)^{p-2} \equiv \frac{n!}{r!(n-r)!} \pmod p$$

우변이 우리가 구하는 값이고, 좌변을 계산해 주면 된다. 드디어 곱셈 형식으로 바꿨으니 항등식의 성질을 마구 활용할 수 있다.

이제 새로운 문제에 부딪혔다. $p-2$승을 구해줘야 하는데, 이걸 그냥 구하면 무려 $1,000,000,000$번 가량 곱셈을 해 주어야 한다. 다행히 어떤 수의 $n$제곱은 분할정복을 통해 $O(\log n)$의 시간복잡도로 구할 수 [있다](https://st-lab.tistory.com/237). 링크된 글에 나오는 모듈러의 특징이 이 글에서 설명한 합동식의 2번과 3번 성질이다.

이를 구현한 코드는 다음과 같다:

{% raw %}
```cpp
// https://www.acmicpc.net/problem/11401
#include <iostream>

using namespace std;

#define MOD 1'000'000'007

long long fac(int n) {
    long long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
        result %= MOD;
    }
    return result;
}

long long pow(long long a, long long n) {
    long long result = 1;
    while (n > 0) {
        if (n % 2) {
            result *= a;
            result %= MOD;
        }
        n >>= 1;

        a *= a;
        a %= MOD;
    }
    return result;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N, K;
    cin >> N >> K;

    long long top = fac(N);
    long long bottom = (fac(K) * fac(N - K)) % MOD;

    cout << (top * pow(bottom, MOD - 2)) % MOD << "\n";

    return 0;
}
```
{% endraw %}

![11401번 제출 결과](/assets/img/posts/fermat/fermat_velog_result_1.png)

### [백준 13977](https://www.acmicpc.net/problem/13977)

> $M$개의 자연수 $N$과 정수 $K$가 주어졌을 때 이항 계수 $\binom{N}{K}$를 $1,000,000,007$로 나눈 나머지를 구하는 프로그램을 작성하시오.

위 문제와 아주 비슷한 문제다. 다만, 계산 횟수가 많아지다 보니 팩토리얼 계산하다가 시간초과가 나게 된다. 따라서 이 문제를 풀 때에는 팩토리얼을 배열에 미리 저장해 놓고 필요할 때마다 꺼내 쓰자. 400만 팩토리얼까지의 계산은 $O(n)$ 시간복잡도로 계산 가능하다.

이를 구현한 코드는 다음과 같다:

{% raw %}
```cpp
// https://www.acmicpc.net/problem/13977
#include <iostream>
#include <vector>

using namespace std;

#define MOD 1'000'000'007
#define FAC_COUNT 4000001

vector<long long> facs(4000001);

long long pow(long long a, long long n) {
    long long result = 1;
    while (n > 0) {
        if (n % 2) {
            result *= a;
            result %= MOD;
        }
        a *= a;
        a %= MOD;
        n /= 2;
    }
    return result;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    facs[0] = 1;
    facs[1] = 1;
    for (int i = 2; i < FAC_COUNT; i++) {
        facs[i] = (facs[i - 1] * i) % MOD;
    }

    int M;
    cin >> M;
    while (M--) {
        int N, K;
        cin >> N >> K;

        long long top = facs[N];
        long long bottom = (facs[K] * facs[N - K]) % MOD;

        cout << (top * pow(bottom, MOD - 2)) % MOD << "\n";
    }

    return 0;
}
```
{% endraw %}

![13977번 제출 결과](/assets/img/posts/fermat/fermat_velog_result_2.png)

## 7. 후기

플레 5 문제들을 모아놓고 푸는데 이 문제를 만났다. 도저히 모르겠어서 검색해 봤더니 이런 내용들이 나왔다. 처음부터 합동식이 나왔는데 이게 뭔지를 모르니 하나도 이해할 수 없었다. 그래서 이 글을 적기 시작했다.

정수론을 제대로 파고든 건 이번이 처음인 것 같다. 다음에 또 수학에서 막히면 여기에 남겨놔야겠다. 혹시 나처럼 아무것도 모르는 사람이 있다면 이 글을 보고 이해할 수 있었으면 좋겠다.

## 참고한 글

1. <https://blog.naver.com/dgsw102/221234184168>
2. <https://rebro.kr/105>
3. <https://namu.wiki/w/%ED%8E%98%EB%A5%B4%EB%A7%88%EC%9D%98%20%EC%86%8C%EC%A0%95%EB%A6%AC>
4. <https://dimenchoi.tistory.com/50>
5. <https://st-lab.tistory.com/237>
6. <https://www.acmicpc.net/blog/view/29>