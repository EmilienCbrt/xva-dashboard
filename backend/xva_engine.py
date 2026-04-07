import QuantLib as ql
import numpy as np

def get_simulated_estr_rate():
    return 0.0225


def get_simulated_euribor_6m_rate():
    return 0.0240

def build_irs_payer(notional, start_date, maturity_date, fixed_rate, index_6m, discount_handle, daycount, calendar):
    schedule = ql.Schedule(
        start_date, maturity_date, ql.Period(ql.Semiannual), calendar,
        ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False
    )
    swap = ql.VanillaSwap(
        ql.VanillaSwap.Payer,
        notional,
        schedule,
        fixed_rate,
        daycount,
        schedule,
        index_6m,
        0.0,
        daycount
    )
    engine = ql.DiscountingSwapEngine(discount_handle)
    swap.setPricingEngine(engine)
    return swap


def build_irs_receiver(notional, start_date, maturity_date, fixed_rate, index_6m, discount_handle, daycount, calendar):
    schedule = ql.Schedule(
        start_date, maturity_date, ql.Period(ql.Semiannual), calendar,
        ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False
    )
    swap = ql.VanillaSwap(
        ql.VanillaSwap.Receiver,
        notional,
        schedule,
        fixed_rate,
        daycount,
        schedule,
        index_6m,
        0.0,
        daycount
    )
    engine = ql.DiscountingSwapEngine(discount_handle)
    swap.setPricingEngine(engine)
    return swap


def build_zero_coupon_bond(notional, start_date, maturity_date, discount_handle, calendar):
    bond = ql.ZeroCouponBond(
        2,
        calendar,
        notional,
        maturity_date,
        ql.ModifiedFollowing,
        100.0,
        start_date
    )
    engine = ql.DiscountingBondEngine(discount_handle)
    bond.setPricingEngine(engine)
    return bond


def build_fra_6x12(notional, today, fixed_rate, index_6m, discount_handle, calendar):
    start_date = calendar.advance(today, ql.Period(6, ql.Months))
    end_date = calendar.advance(today, ql.Period(12, ql.Months))

    fra = ql.ForwardRateAgreement(
        index_6m,
        start_date,
        end_date,
        ql.Position.Long,
        fixed_rate,
        notional,
        discount_handle,
    )
    return fra, start_date


def build_cap(notional, start_date, maturity_date, strike, index_6m, daycount, calendar, discount_handle, cap_vol=0.01):
    schedule = ql.Schedule(
        start_date, maturity_date, ql.Period(ql.Semiannual), calendar,
        ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False
    )
    floating_leg = ql.IborLeg([notional], schedule, index_6m, daycount)
    cap = ql.Cap(floating_leg, [strike])

    vol_handle = ql.QuoteHandle(ql.SimpleQuote(cap_vol))
    engine = ql.BachelierCapFloorEngine(discount_handle, vol_handle)
    cap.setPricingEngine(engine)

    return cap


def build_swaption_5y_into_5y(notional, start_date, fixed_rate, index_6m, daycount, calendar, discount_handle, vol=0.01, payer=True):
    exercise_date = calendar.advance(start_date, ql.Period(5, ql.Years))
    maturity_date = calendar.advance(exercise_date, ql.Period(5, ql.Years))

    schedule = ql.Schedule(
        exercise_date, maturity_date, ql.Period(ql.Semiannual), calendar,
        ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False
    )

    swap_type = ql.VanillaSwap.Payer if payer else ql.VanillaSwap.Receiver

    underlying = ql.VanillaSwap(
        swap_type,
        notional,
        schedule,
        fixed_rate,
        daycount,
        schedule,
        index_6m,
        0.0,
        daycount
    )

    exercise = ql.EuropeanExercise(exercise_date)
    swaption = ql.Swaption(underlying, exercise)

    vol_handle = ql.QuoteHandle(ql.SimpleQuote(vol))
    engine = ql.BachelierSwaptionEngine(discount_handle, vol_handle)
    swaption.setPricingEngine(engine)

    return swaption, exercise_date


def compute_cva(times, dates, expected_exposure, base_discount_curve, end_date=None, recovery_rate=0.40, default_intensity=0.02):
    LGD = 1 - recovery_rate
    cva = 0.0
    for j in range(1, len(times)):
        if end_date is not None and dates[j] > end_date:
            break
        prob_default = np.exp(-default_intensity * times[j - 1]) - np.exp(-default_intensity * times[j])
        avg_exposure = 0.5 * (expected_exposure[j] + expected_exposure[j - 1])
        df = base_discount_curve.discount(dates[j])
        cva += LGD * prob_default * avg_exposure * df
    return cva


def compute_dva(times, dates, expected_exposure_neg, base_discount_curve, end_date=None, own_recovery_rate=0.40, own_default_intensity=0.01):
    own_LGD = 1 - own_recovery_rate
    dva = 0.0
    for j in range(1, len(times)):
        if end_date is not None and dates[j] > end_date:
            break
        prob_own_default = np.exp(-own_default_intensity * times[j - 1]) - np.exp(-own_default_intensity * times[j])
        avg_neg_exposure = 0.5 * (expected_exposure_neg[j] + expected_exposure_neg[j - 1])
        df = base_discount_curve.discount(dates[j])
        dva += own_LGD * prob_own_default * avg_neg_exposure * df
    return dva


def compute_fva(times, dates, expected_exposure, base_discount_curve, end_date=None, funding_spread=0.01):
    fva = 0.0
    for j in range(1, len(times)):
        if end_date is not None and dates[j] > end_date:
            break
        dt_step = times[j] - times[j - 1]
        df = base_discount_curve.discount(dates[j])
        avg_exposure = 0.5 * (expected_exposure[j] + expected_exposure[j - 1])
        fva += funding_spread * avg_exposure * df * dt_step
    return fva


def compute_kva(times, dates, expected_exposure, base_discount_curve, end_date=None, RW=1.0, CR=0.08, cost_of_capital=0.10):
    kva = 0.0
    for j in range(1, len(times)):
        if end_date is not None and dates[j] > end_date:
            break
        dt_step = times[j] - times[j - 1]
        df = base_discount_curve.discount(dates[j])
        avg_exposure = 0.5 * (expected_exposure[j] + expected_exposure[j - 1])
        capital_t = RW * CR * avg_exposure
        kva += cost_of_capital * capital_t * df * dt_step
    return kva


def sigma_piecewise(t, knots, vals):
    for i in range(len(knots) - 1):
        if knots[i] <= t < knots[i + 1]:
            return vals[i]
    return vals[-1]


def run_xva(selected_instruments, notional, product_param, volatility):
    today = ql.Date(8, 2, 2026)
    ql.Settings.instance().evaluationDate = today
    ql.Settings.instance().enforcesTodaysHistoricFixings = False

    calendar = ql.TARGET()
    daycount = ql.Actual360()

    str_flat_rate = get_simulated_estr_rate()
    euribor_flat_rate = get_simulated_euribor_6m_rate()

    base_discount_curve = ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(str_flat_rate)), daycount)
    discount_handle = ql.RelinkableYieldTermStructureHandle(base_discount_curve)

    base_forward_curve = ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(euribor_flat_rate)), daycount)
    forward_handle = ql.RelinkableYieldTermStructureHandle(base_forward_curve)
    index_6m = ql.Euribor6M(forward_handle)

    fixing_date = calendar.advance(today, -2, ql.Days)
    fixing_rate = euribor_flat_rate
    index_6m.addFixing(fixing_date, fixing_rate)

    all_products = {}
    all_end_dates = {}

    irs5_payer = build_irs_payer(
        notional,
        today,
        ql.Date(8, 2, 2031),
        product_param,  # au lieu de 0.02
        index_6m,
        discount_handle,
        daycount,
        calendar
    ) 
    all_products["IRS"] = irs5_payer
    all_end_dates["IRS"] = irs5_payer.maturityDate()

    fra_6x12, fra_start = build_fra_6x12(
        notional,
        today,
        product_param,  # au lieu de 0.025
        index_6m,
        discount_handle,
        calendar
    )
    all_products["FRA"] = fra_6x12
    all_end_dates["FRA"] = fra_start

    cap5 = build_cap(
        notional,
        today,
        ql.Date(8, 2, 2031),
        product_param,
        index_6m,
        daycount,
        calendar,
        discount_handle,
        cap_vol=volatility
    )
    all_products["Cap"] = cap5
    all_end_dates["Cap"] = cap5.maturityDate()

    swaption_5x5_payer, swaption_exercise = build_swaption_5y_into_5y(
        notional,
        today,
        product_param,
        index_6m,
        daycount,
        calendar,
        discount_handle,
        vol=volatility
    )
    all_products["Swaption"] = swaption_5x5_payer
    all_end_dates["Swaption"] = swaption_exercise

    zc7 = build_zero_coupon_bond(notional, today, ql.Date(8, 2, 2033), discount_handle, calendar)
    all_products["Zero Coupon Bond"] = zc7
    all_end_dates["Zero Coupon Bond"] = zc7.maturityDate()

    products = [all_products[name] for name in selected_instruments if name in all_products]
    product_names = [name for name in selected_instruments if name in all_products]
    product_end_dates = {i: all_end_dates[name] for i, name in enumerate(product_names)}
    theoretical_value = products[0].NPV() if products else 0.0

    num_months = 120
    dates = [calendar.advance(today, ql.Period(i, ql.Months)) for i in range(num_months + 1)]
    dates = dates[1:]
    times = [daycount.yearFraction(today, d) for d in dates]
    num_paths = 300

    a_str = 0.06
    a_fwd = 0.05
    rho = 0.8

    sigma_str_times = [0.0, 1.0, 3.0, 5.0, 7.5]
    sigma_str_vals = [0.011, 0.010, 0.009, 0.0085, 0.008]

    sigma_fwd_times = [0.0, 1.0, 3.0, 5.0, 7.5]
    sigma_fwd_vals = [0.014, 0.012, 0.010, 0.009, 0.008]

    rng = np.random.default_rng(1234)

    npvs_by_product = {k: [] for k in range(len(products))}

    for _ in range(num_paths):
        ql.IndexManager.instance().clearHistory(index_6m.name())

        initial_fixing_date = calendar.advance(today, -2, ql.Days)
        index_6m.addFixing(initial_fixing_date, fixing_rate)

        r_str = str_flat_rate
        r_fwd = euribor_flat_rate

        path_npvs = {k: [] for k in range(len(products))}
        prev_t = 0.0

        for j, t in enumerate(times):
            dt_step = t - prev_t
            prev_t = t

            z1 = rng.standard_normal()
            z2 = rho * z1 + np.sqrt(1 - rho ** 2) * rng.standard_normal()

            sig_str = sigma_piecewise(t, sigma_str_times, sigma_str_vals)
            sig_fwd = sigma_piecewise(t, sigma_fwd_times, sigma_fwd_vals)

            theta_str = str_flat_rate
            theta_fwd = euribor_flat_rate

            r_str = r_str + a_str * (theta_str - r_str) * dt_step + sig_str * np.sqrt(dt_step) * z1
            r_fwd = r_fwd + a_fwd * (theta_fwd - r_fwd) * dt_step + sig_fwd * np.sqrt(dt_step) * z2

            eval_date = dates[j]
            ql.Settings.instance().evaluationDate = eval_date

            temp_discount_curve = ql.FlatForward(eval_date, ql.QuoteHandle(ql.SimpleQuote(r_str)), daycount)
            temp_forward_curve = ql.FlatForward(eval_date, ql.QuoteHandle(ql.SimpleQuote(r_fwd)), daycount)

            discount_handle.linkTo(temp_discount_curve)
            forward_handle.linkTo(temp_forward_curve)

            fixing_date = calendar.advance(eval_date, -2, ql.Days)
            try:
                index_6m.addFixing(fixing_date, r_fwd)
            except RuntimeError:
                pass

            for k, instr in enumerate(products):
                end_date = product_end_dates.get(k)
                if eval_date > end_date:
                    path_npvs[k].append(0.0)
                else:
                    path_npvs[k].append(instr.NPV())

        for k in range(len(products)):
            npvs_by_product[k].append(path_npvs[k])

    ql.Settings.instance().evaluationDate = today
    discount_handle.linkTo(base_discount_curve)
    forward_handle.linkTo(base_forward_curve)

    ee_by_product = {}
    ene_by_product = {}

    for k in range(len(products)):
        all_npvs_k = np.array(npvs_by_product[k])
        exposures_k = np.maximum(all_npvs_k, 0)
        exposures_neg_k = np.maximum(-all_npvs_k, 0)

        ee_by_product[k] = np.mean(exposures_k, axis=0)
        ene_by_product[k] = np.mean(exposures_neg_k, axis=0)

    total_cva = 0.0
    total_dva = 0.0
    total_fva = 0.0
    total_kva = 0.0

    for k in range(len(products)):
        cva = compute_cva(times, dates, ee_by_product[k], base_discount_curve, product_end_dates[k])
        dva = compute_dva(times, dates, ene_by_product[k], base_discount_curve, product_end_dates[k])
        fva = compute_fva(times, dates, ee_by_product[k], base_discount_curve, product_end_dates[k])
        kva = compute_kva(times, dates, ee_by_product[k], base_discount_curve, product_end_dates[k])

        total_cva += cva
        total_dva += dva
        total_fva += fva
        total_kva += kva

    portfolio_ee = []
    portfolio_ene = []
    cumulative_cva = []
    cumulative_dva = []

    running_cva = 0.0
    running_dva = 0.0

    for j in range(len(times)):
        total_ee_t = sum(ee_by_product[k][j] for k in range(len(products)))
        total_ene_t = sum(ene_by_product[k][j] for k in range(len(products)))

        portfolio_ee.append({
            "time": round(times[j], 2),
            "value": float(total_ee_t)
        })

        portfolio_ene.append({
            "time": round(times[j], 2),
            "value": float(total_ene_t)
        })

    recovery_rate = 0.40
    own_recovery_rate = 0.40
    default_intensity = 0.02
    own_default_intensity = 0.01

    LGD = 1 - recovery_rate
    own_LGD = 1 - own_recovery_rate

    for j in range(1, len(times)):
        prob_default = np.exp(-default_intensity * times[j - 1]) - np.exp(-default_intensity * times[j])
        prob_own_default = np.exp(-own_default_intensity * times[j - 1]) - np.exp(-own_default_intensity * times[j])

        avg_ee = 0.5 * (portfolio_ee[j]["value"] + portfolio_ee[j - 1]["value"])
        avg_ene = 0.5 * (portfolio_ene[j]["value"] + portfolio_ene[j - 1]["value"])

        df = base_discount_curve.discount(dates[j])

        incr_cva = LGD * prob_default * avg_ee * df
        incr_dva = own_LGD * prob_own_default * avg_ene * df

        running_cva += incr_cva
        running_dva += incr_dva

        cumulative_cva.append({
            "time": round(times[j], 2),
            "value": float(running_cva)
        })

        cumulative_dva.append({
            "time": round(times[j], 2),
            "value": float(running_dva)
        })

    return {
        "theoretical_value": float(theoretical_value),
        "CVA": float(total_cva),
        "DVA": float(total_dva),
        "FVA": float(total_fva),
        "KVA": float(total_kva),
        "exposure": portfolio_ee,
        "ene": portfolio_ene,
        "cva_curve": cumulative_cva,
        "dva_curve": cumulative_dva
    }